"""
Copy Trading Executor Service

리더의 주문을 팔로워에게 자동 복제
- 포지션 크기 자동 조정 (copy_ratio)
- 잔고 확인 및 리스크 관리
- 비동기 병렬 주문 실행
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import logging
import asyncio

from app.models.copy_trading import CopyRelationship, CopiedTrade
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.trading import Trade
from app.services.binance_client import BinanceClient
from app.services.okx_client import OKXClient
from app.core.crypto import crypto_service

logger = logging.getLogger(__name__)


class CopyTradingExecutor:
    """카피 트레이딩 실행 서비스"""

    def __init__(self, db: Session):
        self.db = db

    async def get_exchange_client(self, api_key: ApiKey):
        """
        Get exchange client instance

        Args:
            api_key: ApiKey model with encrypted credentials

        Returns:
            Exchange client (BinanceClient or OKXClient)
        """
        # Decrypt API credentials
        decrypted = crypto_service.decrypt_api_credentials({
            "api_key": api_key.api_key,
            "api_secret": api_key.api_secret,
            "passphrase": api_key.passphrase if hasattr(api_key, 'passphrase') else None
        })

        if api_key.exchange.lower() == "binance":
            return BinanceClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                testnet=api_key.testnet
            )
        elif api_key.exchange.lower() == "okx":
            return OKXClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                passphrase=decrypted["passphrase"],
                testnet=api_key.testnet
            )
        else:
            raise ValueError(f"Unsupported exchange: {api_key.exchange}")

    async def execute_copied_order(
        self,
        copy_relationship: CopyRelationship,
        leader_trade: Trade,
        leader_order: Dict
    ) -> Dict:
        """
        Execute a copied order for a follower

        Args:
            copy_relationship: CopyRelationship instance
            leader_trade: Leader's Trade record
            leader_order: Leader's order details

        Returns:
            Dict with execution results
        """
        start_time = datetime.utcnow()

        try:
            # Check if follower can copy
            can_copy, reason = copy_relationship.can_copy_trade()
            if not can_copy:
                logger.warning(f"Cannot copy trade: {reason}")
                return {"success": False, "error": reason}

            # Get follower's API key
            follower_api_key = self.db.query(ApiKey).filter(
                ApiKey.user_id == copy_relationship.follower_id,
                ApiKey.exchange == leader_order["exchange"],
                ApiKey.is_active == True
            ).first()

            if not follower_api_key:
                error_msg = f"Follower has no active API key for {leader_order['exchange']}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            # Get exchange client
            client = await self.get_exchange_client(follower_api_key)

            # Calculate follower's position size
            follower_quantity = copy_relationship.calculate_position_size(
                leader_position_size=leader_order["quantity"],
                leader_price=leader_order["price"]
            )

            if follower_quantity == 0:
                error_msg = "Position size too small after copy ratio"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg}

            # Check follower's balance
            account_info = await client.get_account_balance()
            available_balance = float(account_info.get("available_balance", 0))

            required_balance = follower_quantity * leader_order["price"]
            if available_balance < required_balance:
                error_msg = f"Insufficient balance: {available_balance} < {required_balance}"
                logger.warning(error_msg)
                return {"success": False, "error": error_msg}

            # Execute order based on side
            order_result = None
            if leader_order["side"] in ["buy", "long"]:
                order_result = await client.create_market_order(
                    symbol=leader_order["symbol"],
                    side="buy",
                    quantity=follower_quantity
                )
            elif leader_order["side"] in ["sell", "short"]:
                order_result = await client.create_market_order(
                    symbol=leader_order["symbol"],
                    side="sell",
                    quantity=follower_quantity
                )
            elif leader_order["side"] in ["close_long", "close_short", "close"]:
                order_result = await client.close_position(
                    symbol=leader_order["symbol"],
                    side=leader_order["side"]
                )

            if not order_result or order_result.get("status") != "FILLED":
                error_msg = f"Order execution failed: {order_result}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "order_result": order_result}

            # Calculate execution time
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Create CopiedTrade record
            copied_trade = CopiedTrade(
                copy_relationship_id=copy_relationship.id,
                leader_trade_id=leader_trade.id if leader_trade else None,
                leader_order_id=leader_order.get("order_id"),
                follower_order_id=order_result.get("order_id"),
                symbol=leader_order["symbol"],
                side=leader_order["side"],
                order_type=leader_order.get("order_type", "market"),
                leader_quantity=leader_order["quantity"],
                follower_quantity=follower_quantity,
                leader_entry_price=leader_order["price"],
                follower_entry_price=order_result.get("price"),
                copy_ratio_used=copy_relationship.copy_ratio,
                status="executed",
                execution_time_ms=execution_time_ms,
                leader_order_time=leader_order.get("timestamp"),
                follower_order_time=datetime.utcnow()
            )
            copied_trade.calculate_slippage()
            self.db.add(copied_trade)

            # Update copy relationship stats
            copy_relationship.record_copy_attempt(success=True)

            self.db.commit()

            logger.info(
                f"✅ Copied trade: {copy_relationship.follower_id} -> "
                f"{leader_order['symbol']} {leader_order['side']} "
                f"{follower_quantity} @ {order_result.get('price')}"
            )

            return {
                "success": True,
                "copied_trade_id": copied_trade.id,
                "follower_order_id": order_result.get("order_id"),
                "quantity": follower_quantity,
                "price": order_result.get("price"),
                "execution_time_ms": execution_time_ms,
                "slippage": copied_trade.slippage
            }

        except Exception as e:
            logger.error(f"Error executing copied order: {e}", exc_info=True)

            # Record failed copy attempt
            copy_relationship.record_copy_attempt(success=False)

            # Create failed CopiedTrade record
            copied_trade = CopiedTrade(
                copy_relationship_id=copy_relationship.id,
                leader_trade_id=leader_trade.id if leader_trade else None,
                symbol=leader_order.get("symbol", "UNKNOWN"),
                side=leader_order.get("side", "UNKNOWN"),
                leader_quantity=leader_order.get("quantity", 0),
                follower_quantity=0,
                copy_ratio_used=copy_relationship.copy_ratio,
                status="failed",
                error_message=str(e),
                leader_order_time=leader_order.get("timestamp")
            )
            self.db.add(copied_trade)
            self.db.commit()

            return {"success": False, "error": str(e)}

    async def replicate_order(
        self,
        leader_user_id: str,
        leader_order: Dict,
        leader_trade: Optional[Trade] = None
    ) -> List[Dict]:
        """
        Replicate leader's order to all active followers

        Args:
            leader_user_id: Leader's user ID
            leader_order: Order details dict
            leader_trade: Optional Trade record

        Returns:
            List of execution results for each follower
        """
        # Get all active copy relationships for this leader
        copy_relationships = self.db.query(CopyRelationship).filter(
            CopyRelationship.leader_id == leader_user_id,
            CopyRelationship.is_active == True
        ).all()

        if not copy_relationships:
            logger.debug(f"No active followers for leader {leader_user_id}")
            return []

        logger.info(
            f"📋 Replicating order for {len(copy_relationships)} followers: "
            f"{leader_order['symbol']} {leader_order['side']}"
        )

        # Execute all copies in parallel
        tasks = []
        for relationship in copy_relationships:
            task = self.execute_copied_order(relationship, leader_trade, leader_order)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log summary
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed = len(results) - successful
        logger.info(
            f"✅ Copy replication complete: {successful} succeeded, {failed} failed"
        )

        return results

    async def stop_copying(self, copy_relationship_id: str) -> bool:
        """
        Stop copying and optionally close all copied positions

        Args:
            copy_relationship_id: CopyRelationship ID

        Returns:
            Success boolean
        """
        try:
            relationship = self.db.query(CopyRelationship).filter(
                CopyRelationship.id == copy_relationship_id
            ).first()

            if not relationship:
                return False

            relationship.is_active = False
            relationship.paused_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"🛑 Stopped copying: {copy_relationship_id}")
            return True

        except Exception as e:
            logger.error(f"Error stopping copy relationship: {e}")
            self.db.rollback()
            return False

    async def calculate_profit_share(self, copied_trade: CopiedTrade):
        """
        Calculate and record profit share for leader

        Args:
            copied_trade: CopiedTrade instance with PnL
        """
        try:
            if copied_trade.follower_pnl <= 0:
                return  # No profit to share

            relationship = self.db.query(CopyRelationship).filter(
                CopyRelationship.id == copied_trade.copy_relationship_id
            ).first()

            if not relationship:
                return

            # Calculate profit share
            profit_share = copied_trade.follower_pnl * (relationship.profit_share_percentage / 100)

            copied_trade.profit_shared = profit_share
            relationship.total_shared_profit += profit_share
            relationship.pending_payout += profit_share

            self.db.commit()

            logger.info(
                f"💰 Profit share calculated: {profit_share} USDT "
                f"({relationship.profit_share_percentage}% of {copied_trade.follower_pnl})"
            )

        except Exception as e:
            logger.error(f"Error calculating profit share: {e}")
            self.db.rollback()
