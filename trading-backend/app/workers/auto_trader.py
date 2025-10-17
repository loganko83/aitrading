"""
Auto-Trading Engine

Executes trades automatically based on user's selected strategy and AI ensemble signals.
Monitors positions and manages risk in real-time.
"""

import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.services.binance import BinanceFuturesClient
from app.ai.ensemble import TripleAIEnsemble
from app.database.session import get_db
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class AutoTrader:
    """
    Automated trading execution engine

    Responsibilities:
    - Load active strategy configurations for users
    - Run AI ensemble analysis on configured symbols
    - Execute orders when signals meet strategy thresholds
    - Set stop-loss and take-profit automatically
    - Monitor positions and update database
    """

    def __init__(self, user_id: str, db: Session):
        """
        Initialize auto-trader for specific user

        Args:
            user_id: User ID
            db: Database session
        """
        self.user_id = user_id
        self.db = db
        self.is_running = False
        self.binance_client: Optional[BinanceFuturesClient] = None
        self.ai_ensemble = TripleAIEnsemble()

        # Load user
        self.user = db.query(User).filter(User.id == user_id).first()
        if not self.user:
            raise ValueError(f"User {user_id} not found")

        # Load active strategy config
        self.active_config = next(
            (config for config in self.user.strategyConfigs if config.isActive and config.autoTradeEnabled),
            None
        )

        if not self.active_config:
            raise ValueError(f"No active auto-trading strategy found for user {user_id}")

        # Get base strategy
        self.strategy = self.active_config.strategy

        # Apply custom params if exists
        self.params = self._load_strategy_params()

        logger.info(f"AutoTrader initialized for user {user_id} with strategy: {self.strategy.name}")

    def _load_strategy_params(self) -> Dict:
        """Load strategy parameters with custom overrides"""
        # Start with strategy defaults
        params = {
            'mlWeight': self.strategy.mlWeight,
            'gpt4Weight': self.strategy.gpt4Weight,
            'claudeWeight': self.strategy.claudeWeight,
            'taWeight': self.strategy.taWeight,
            'minProbability': self.strategy.minProbability,
            'minConfidence': self.strategy.minConfidence,
            'minAgreement': self.strategy.minAgreement,
            'defaultLeverage': self.strategy.defaultLeverage,
            'positionSizePct': self.strategy.positionSizePct,
            'slAtrMultiplier': self.strategy.slAtrMultiplier,
            'tpAtrMultiplier': self.strategy.tpAtrMultiplier,
            'maxOpenPositions': self.strategy.maxOpenPositions,
            'atrPeriod': self.strategy.atrPeriod,
            'rsiPeriod': self.strategy.rsiPeriod,
            'macdFast': self.strategy.macdFast,
            'macdSlow': self.strategy.macdSlow,
            'macdSignal': self.strategy.macdSignal,
        }

        # Apply custom overrides
        if self.active_config.customParams:
            params.update(self.active_config.customParams)

        return params

    async def initialize_binance(self):
        """Initialize Binance client with user's API keys"""
        # Load user's API key from database
        api_key_record = next(
            (key for key in self.user.apiKeys if key.isActive and key.exchange == 'binance'),
            None
        )

        if not api_key_record:
            raise ValueError(f"No active Binance API key found for user {self.user_id}")

        # TODO: Decrypt API key and secret
        # For now, use from record directly (assuming they're decrypted)
        api_key = api_key_record.apiKey
        api_secret = api_key_record.apiSecret

        self.binance_client = BinanceFuturesClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=settings.BINANCE_TESTNET
        )

        logger.info(f"Binance client initialized for user {self.user_id}")

    async def start(self):
        """Start auto-trading loop"""
        if self.is_running:
            logger.warning(f"AutoTrader already running for user {self.user_id}")
            return

        self.is_running = True
        logger.info(f"Starting AutoTrader for user {self.user_id}...")

        # Initialize Binance client
        await self.initialize_binance()

        try:
            while self.is_running:
                await self._trading_cycle()

                # Wait before next cycle (e.g., 5 minutes)
                await asyncio.sleep(300)  # 5 minutes

        except Exception as e:
            logger.error(f"Error in auto-trading loop: {e}", exc_info=True)
            self.is_running = False
            raise

    async def stop(self):
        """Stop auto-trading loop"""
        logger.info(f"Stopping AutoTrader for user {self.user_id}...")
        self.is_running = False

    async def _trading_cycle(self):
        """Execute one trading cycle"""
        logger.info(f"--- Trading Cycle Start for {self.user_id} ---")

        try:
            # 1. Get account balance
            balance = await self.binance_client.get_account_balance()
            available_balance = balance['availableBalance']

            logger.info(f"Available balance: ${available_balance:.2f}")

            # 2. Get current open positions
            open_positions = await self.binance_client.get_open_positions()

            logger.info(f"Open positions: {len(open_positions)} / {self.params['maxOpenPositions']}")

            # 3. Check if we can open new positions
            if len(open_positions) >= self.params['maxOpenPositions']:
                logger.info("Max open positions reached, skipping new signals")
                return

            # 4. Analyze each configured symbol
            for symbol in self.active_config.selectedSymbols:
                # Skip if already have position in this symbol
                if any(pos['symbol'] == symbol for pos in open_positions):
                    logger.info(f"Already have position in {symbol}, skipping")
                    continue

                # Get market data
                market_data = await self.binance_client.get_market_data(
                    symbol=symbol,
                    interval='1h',
                    limit=500
                )

                # Get current price
                current_price = await self.binance_client.get_current_price(symbol)

                # Run AI ensemble analysis
                decision = await self.ai_ensemble.analyze(
                    symbol=symbol,
                    market_data=market_data,
                    current_price=current_price
                )

                # Log decision
                logger.info(f"{symbol}: {decision.direction} | "
                          f"Prob={decision.probability_up:.2%} | "
                          f"Conf={decision.confidence:.2%} | "
                          f"Agree={decision.agreement:.2%} | "
                          f"Enter={decision.should_enter}")

                # 5. Execute trade if signal meets criteria
                if decision.should_enter:
                    await self._execute_trade(
                        symbol=symbol,
                        decision=decision,
                        available_balance=available_balance
                    )

            logger.info(f"--- Trading Cycle End for {self.user_id} ---")

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)

    async def _execute_trade(
        self,
        symbol: str,
        decision,
        available_balance: float
    ):
        """Execute a trade based on AI decision"""
        try:
            logger.info(f"🚀 Executing trade for {symbol} ({decision.direction})")

            # 1. Set leverage
            leverage = self.params['defaultLeverage']
            await self.binance_client.set_leverage(symbol=symbol, leverage=leverage)

            # 2. Calculate position size
            position_size_usd = available_balance * self.params['positionSizePct']

            # Calculate quantity (accounting for leverage)
            quantity = (position_size_usd * leverage) / decision.entry_price

            # Round to appropriate precision (e.g., BTC = 3 decimals)
            quantity = round(quantity, 3)

            logger.info(f"Position size: ${position_size_usd:.2f} | Quantity: {quantity} | Leverage: {leverage}x")

            # 3. Place market order
            side = 'BUY' if decision.direction == 'LONG' else 'SELL'

            order = await self.binance_client.place_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity
            )

            logger.info(f"✅ Market order placed: {order['orderId']}")

            # 4. Set stop-loss
            sl_side = 'SELL' if decision.direction == 'LONG' else 'BUY'
            stop_loss_order = await self.binance_client.set_stop_loss(
                symbol=symbol,
                side=sl_side,
                quantity=quantity,
                stop_price=decision.stop_loss
            )

            logger.info(f"🛡️ Stop-loss set @ {decision.stop_loss}")

            # 5. Set take-profit
            take_profit_order = await self.binance_client.set_take_profit(
                symbol=symbol,
                side=sl_side,
                quantity=quantity,
                take_profit_price=decision.take_profit
            )

            logger.info(f"🎯 Take-profit set @ {decision.take_profit}")

            # 6. Save to database
            await self._save_position_to_db(
                symbol=symbol,
                decision=decision,
                quantity=quantity,
                leverage=leverage,
                order_id=order['orderId']
            )

            # 7. Update strategy stats
            self.active_config.totalTrades += 1
            self.db.commit()

            logger.info(f"✨ Trade execution completed for {symbol}")

        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {e}", exc_info=True)
            self.db.rollback()

    async def _save_position_to_db(
        self,
        symbol: str,
        decision,
        quantity: float,
        leverage: int,
        order_id: str
    ):
        """Save opened position to database"""
        from app.models.position import Position

        try:
            position = Position(
                userId=self.user_id,
                symbol=symbol,
                side=decision.direction,
                quantity=quantity,
                entryPrice=decision.entry_price,
                currentPrice=decision.entry_price,
                stopLoss=decision.stop_loss,
                takeProfit=decision.take_profit,
                leverage=leverage,
                unrealizedPnl=0.0,
                status='OPEN',
                aiConfidence=decision.confidence,
                aiReason=decision.reasoning
            )

            self.db.add(position)
            self.db.commit()

            logger.info(f"Position saved to database: {position.id}")

        except Exception as e:
            logger.error(f"Error saving position to database: {e}", exc_info=True)
            self.db.rollback()
            raise


class AutoTraderManager:
    """
    Manages multiple auto-traders for different users
    """

    def __init__(self):
        self.traders: Dict[str, AutoTrader] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    async def start_trader(self, user_id: str, db: Session):
        """Start auto-trading for a user"""
        if user_id in self.traders:
            logger.warning(f"Trader already running for user {user_id}")
            return

        try:
            # Create trader instance
            trader = AutoTrader(user_id=user_id, db=db)
            self.traders[user_id] = trader

            # Start trading loop in background task
            task = asyncio.create_task(trader.start())
            self.tasks[user_id] = task

            logger.info(f"Auto-trader started for user {user_id}")

        except Exception as e:
            logger.error(f"Error starting trader for user {user_id}: {e}", exc_info=True)
            raise

    async def stop_trader(self, user_id: str):
        """Stop auto-trading for a user"""
        if user_id not in self.traders:
            logger.warning(f"No trader running for user {user_id}")
            return

        try:
            # Stop trader
            trader = self.traders[user_id]
            await trader.stop()

            # Cancel task
            task = self.tasks[user_id]
            task.cancel()

            # Remove from managers
            del self.traders[user_id]
            del self.tasks[user_id]

            logger.info(f"Auto-trader stopped for user {user_id}")

        except Exception as e:
            logger.error(f"Error stopping trader for user {user_id}: {e}", exc_info=True)
            raise

    def get_trader_status(self, user_id: str) -> Dict:
        """Get status of a trader"""
        if user_id not in self.traders:
            return {
                'isRunning': False,
                'message': 'Trader not running'
            }

        trader = self.traders[user_id]
        return {
            'isRunning': trader.is_running,
            'userId': trader.user_id,
            'strategyName': trader.strategy.name,
            'symbols': trader.active_config.selectedSymbols,
            'message': 'Trader running'
        }

    def list_active_traders(self) -> List[Dict]:
        """List all active traders"""
        return [
            {
                'userId': user_id,
                'strategyName': trader.strategy.name,
                'symbols': trader.active_config.selectedSymbols
            }
            for user_id, trader in self.traders.items()
        ]


# Global auto-trader manager instance
auto_trader_manager = AutoTraderManager()
