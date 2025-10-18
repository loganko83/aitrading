"""
주문 실행 서비스

Features:
- TradingView 시그널 → 실제 주문 변환
- Binance/OKX 자동 주문 실행
- 리스크 관리 (포지션 크기, 레버리지)
- 에러 처리 및 재시도
"""

from typing import Dict, Any, Optional
from enum import Enum
import logging

from app.services.binance_client import BinanceClient
from app.services.okx_client import OKXClient
from app.core.stability import with_retry, RetryStrategy

logger = logging.getLogger(__name__)


class Exchange(str, Enum):
    """거래소"""
    BINANCE = "binance"
    OKX = "okx"


class SignalType(str, Enum):
    """시그널 타입"""
    LONG = "long"
    SHORT = "short"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    CLOSE_ALL = "close_all"


class OrderExecutor:
    """주문 실행 서비스"""

    def __init__(self):
        self.binance_clients: Dict[str, BinanceClient] = {}
        self.okx_clients: Dict[str, OKXClient] = {}

    def register_binance_account(
        self,
        account_id: str,
        api_key: str,
        api_secret: str,
        testnet: bool = True
    ):
        """Binance 계정 등록"""
        self.binance_clients[account_id] = BinanceClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        logger.info(f"Binance account registered: {account_id} (testnet={testnet})")

    def register_okx_account(
        self,
        account_id: str,
        api_key: str,
        api_secret: str,
        passphrase: str,
        testnet: bool = True
    ):
        """OKX 계정 등록"""
        self.okx_clients[account_id] = OKXClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=testnet
        )
        logger.info(f"OKX account registered: {account_id} (testnet={testnet})")

    @with_retry(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
    def execute_signal(
        self,
        account_id: str,
        exchange: Exchange,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        TradingView 시그널 실행

        Args:
            account_id: 계정 ID
            exchange: 거래소 (binance or okx)
            signal: 시그널 데이터
                {
                    "action": "long" | "short" | "close_long" | "close_short" | "close_all",
                    "symbol": "BTCUSDT",
                    "price": 50000.0,
                    "quantity": 0.01,  # 선택사항
                    "leverage": 10,     # 선택사항
                    "stop_loss": 48000, # 선택사항
                    "take_profit": 52000 # 선택사항
                }

        Returns:
            실행 결과
        """
        try:
            logger.info(
                f"Executing signal: account={account_id}, exchange={exchange.value}, "
                f"action={signal.get('action')}, symbol={signal.get('symbol')}"
            )

            # 거래소별 실행
            if exchange == Exchange.BINANCE:
                return self._execute_binance_signal(account_id, signal)
            elif exchange == Exchange.OKX:
                return self._execute_okx_signal(account_id, signal)
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")

        except Exception as e:
            logger.error(f"Signal execution failed: {str(e)}", exc_info=True)
            raise

    def _execute_binance_signal(
        self,
        account_id: str,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Binance 시그널 실행"""
        client = self.binance_clients.get(account_id)
        if not client:
            raise ValueError(f"Binance account not found: {account_id}")

        action = SignalType(signal["action"])
        symbol = signal["symbol"]
        quantity = signal.get("quantity")
        leverage = signal.get("leverage")
        stop_loss = signal.get("stop_loss")
        take_profit = signal.get("take_profit")

        results = {}

        # 레버리지 설정
        if leverage:
            results["leverage"] = client.set_leverage(symbol, leverage)

        # 액션별 실행
        if action == SignalType.LONG:
            # 롱 진입
            if not quantity:
                # 수량 미지정 시 계좌의 10% 사용
                balance = client.get_account_balance()
                available = balance["available_balance"]
                quantity = self._calculate_quantity(
                    available * 0.1,
                    signal.get("price", client.get_current_price(symbol)),
                    leverage or 1
                )

            results["entry"] = client.create_market_order(
                symbol=symbol,
                side="BUY",
                quantity=quantity
            )

            # Stop Loss 설정
            if stop_loss:
                results["stop_loss"] = client.create_stop_loss(
                    symbol=symbol,
                    side="SELL",
                    quantity=quantity,
                    stop_price=stop_loss
                )

            # Take Profit 설정
            if take_profit:
                results["take_profit"] = client.create_take_profit(
                    symbol=symbol,
                    side="SELL",
                    quantity=quantity,
                    take_profit_price=take_profit
                )

        elif action == SignalType.SHORT:
            # 숏 진입
            if not quantity:
                balance = client.get_account_balance()
                available = balance["available_balance"]
                quantity = self._calculate_quantity(
                    available * 0.1,
                    signal.get("price", client.get_current_price(symbol)),
                    leverage or 1
                )

            results["entry"] = client.create_market_order(
                symbol=symbol,
                side="SELL",
                quantity=quantity
            )

            # Stop Loss 설정
            if stop_loss:
                results["stop_loss"] = client.create_stop_loss(
                    symbol=symbol,
                    side="BUY",
                    quantity=quantity,
                    stop_price=stop_loss
                )

            # Take Profit 설정
            if take_profit:
                results["take_profit"] = client.create_take_profit(
                    symbol=symbol,
                    side="BUY",
                    quantity=quantity,
                    take_profit_price=take_profit
                )

        elif action in [SignalType.CLOSE_LONG, SignalType.CLOSE_SHORT, SignalType.CLOSE_ALL]:
            # 포지션 청산
            results["close"] = client.close_position(symbol)

        logger.info(f"Binance signal executed successfully: {action.value}")

        return {
            "success": True,
            "exchange": "binance",
            "account_id": account_id,
            "action": action.value,
            "symbol": symbol,
            "results": results
        }

    def _execute_okx_signal(
        self,
        account_id: str,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """OKX 시그널 실행"""
        client = self.okx_clients.get(account_id)
        if not client:
            raise ValueError(f"OKX account not found: {account_id}")

        action = SignalType(signal["action"])
        symbol = signal["symbol"]  # OKX 형식: BTC-USDT-SWAP
        quantity = signal.get("quantity")
        leverage = signal.get("leverage")

        results = {}

        # 레버리지 설정
        if leverage:
            results["leverage"] = client.set_leverage(symbol, leverage)

        # 액션별 실행
        if action == SignalType.LONG:
            # 롱 진입
            if not quantity:
                balance = client.get_account_balance()
                available = balance["available_balance"]
                quantity = self._calculate_quantity(
                    available * 0.1,
                    signal.get("price", client.get_current_price(symbol)),
                    leverage or 1
                )

            results["entry"] = client.create_market_order(
                symbol=symbol,
                side="buy",
                quantity=quantity,
                position_side="long"
            )

        elif action == SignalType.SHORT:
            # 숏 진입
            if not quantity:
                balance = client.get_account_balance()
                available = balance["available_balance"]
                quantity = self._calculate_quantity(
                    available * 0.1,
                    signal.get("price", client.get_current_price(symbol)),
                    leverage or 1
                )

            results["entry"] = client.create_market_order(
                symbol=symbol,
                side="sell",
                quantity=quantity,
                position_side="short"
            )

        elif action in [SignalType.CLOSE_LONG, SignalType.CLOSE_SHORT, SignalType.CLOSE_ALL]:
            # 포지션 청산
            position_side = "long" if action == SignalType.CLOSE_LONG else "short" if action == SignalType.CLOSE_SHORT else "net"
            results["close"] = client.close_position(symbol, position_side=position_side)

        logger.info(f"OKX signal executed successfully: {action.value}")

        return {
            "success": True,
            "exchange": "okx",
            "account_id": account_id,
            "action": action.value,
            "symbol": symbol,
            "results": results
        }

    def _calculate_quantity(
        self,
        capital: float,
        price: float,
        leverage: int
    ) -> float:
        """수량 계산"""
        # 레버리지를 고려한 수량 계산
        quantity = (capital * leverage) / price
        return round(quantity, 3)  # 소수점 3자리

    def get_account_status(
        self,
        account_id: str,
        exchange: Exchange
    ) -> Dict[str, Any]:
        """계정 상태 조회"""
        try:
            if exchange == Exchange.BINANCE:
                client = self.binance_clients.get(account_id)
                if not client:
                    raise ValueError(f"Binance account not found: {account_id}")

                balance = client.get_account_balance()
                positions = client.get_positions()
                open_orders = client.get_open_orders()

                return {
                    "exchange": "binance",
                    "account_id": account_id,
                    "balance": balance,
                    "positions": positions,
                    "open_orders": open_orders
                }

            elif exchange == Exchange.OKX:
                client = self.okx_clients.get(account_id)
                if not client:
                    raise ValueError(f"OKX account not found: {account_id}")

                balance = client.get_account_balance()
                positions = client.get_positions()

                return {
                    "exchange": "okx",
                    "account_id": account_id,
                    "balance": balance,
                    "positions": positions
                }

        except Exception as e:
            logger.error(f"Failed to get account status: {str(e)}")
            raise


# 글로벌 인스턴스
order_executor = OrderExecutor()
