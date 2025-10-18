"""
Binance Futures API 클라이언트

Features:
- 시장가/지정가 주문
- 포지션 관리
- 레버리지 설정
- Stop Loss / Take Profit
"""

from typing import Dict, Any, Optional, List
import hmac
import hashlib
import time
import requests
from datetime import datetime
import logging

from app.core.config import settings
from app.core.stability import with_retry, with_timeout, RetryStrategy

logger = logging.getLogger(__name__)


class BinanceClient:
    """Binance Futures API 클라이언트"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet

        # API URLs
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"

        self.headers = {
            "X-MBX-APIKEY": self.api_key
        }

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """HMAC SHA256 서명 생성"""
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature

    @with_retry(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
    @with_timeout(timeout_seconds=10.0)
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """API 요청"""
        url = f"{self.base_url}{endpoint}"

        if params is None:
            params = {}

        # 서명 필요 시
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._generate_signature(params)

        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, params=params, headers=self.headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, params=params, headers=self.headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Binance API request failed: {str(e)}")
            raise

    def get_account_balance(self) -> Dict[str, Any]:
        """계좌 잔액 조회"""
        result = self._request("GET", "/fapi/v2/balance", signed=True)

        # USDT 잔액만 추출
        usdt_balance = next(
            (item for item in result if item["asset"] == "USDT"),
            {"availableBalance": "0", "balance": "0"}
        )

        return {
            "asset": "USDT",
            "available_balance": float(usdt_balance["availableBalance"]),
            "total_balance": float(usdt_balance["balance"])
        }

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """포지션 조회"""
        params = {}
        if symbol:
            params["symbol"] = symbol

        result = self._request("GET", "/fapi/v2/positionRisk", params=params, signed=True)

        # 활성 포지션만 필터링
        active_positions = [
            {
                "symbol": pos["symbol"],
                "position_amt": float(pos["positionAmt"]),
                "entry_price": float(pos["entryPrice"]),
                "unrealized_pnl": float(pos["unRealizedProfit"]),
                "leverage": int(pos["leverage"]),
                "side": "LONG" if float(pos["positionAmt"]) > 0 else "SHORT" if float(pos["positionAmt"]) < 0 else "NONE"
            }
            for pos in result
            if float(pos["positionAmt"]) != 0
        ]

        return active_positions

    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """레버리지 설정"""
        params = {
            "symbol": symbol,
            "leverage": leverage
        }

        result = self._request("POST", "/fapi/v1/leverage", params=params, signed=True)

        logger.info(f"Leverage set: {symbol} = {leverage}x")

        return {
            "symbol": result["symbol"],
            "leverage": result["leverage"],
            "max_notional_value": result.get("maxNotionalValue", "N/A")
        }

    def create_market_order(
        self,
        symbol: str,
        side: str,  # BUY or SELL
        quantity: float,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """시장가 주문"""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity
        }

        if reduce_only:
            params["reduceOnly"] = "true"

        result = self._request("POST", "/fapi/v1/order", params=params, signed=True)

        logger.info(
            f"Market order created: {symbol} {side} {quantity} "
            f"(orderId: {result['orderId']})"
        )

        return {
            "order_id": result["orderId"],
            "symbol": result["symbol"],
            "side": result["side"],
            "type": result["type"],
            "quantity": float(result["origQty"]),
            "status": result["status"],
            "timestamp": result["updateTime"]
        }

    def create_limit_order(
        self,
        symbol: str,
        side: str,  # BUY or SELL
        quantity: float,
        price: float,
        time_in_force: str = "GTC"  # GTC, IOC, FOK
    ) -> Dict[str, Any]:
        """지정가 주문"""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": quantity,
            "price": price,
            "timeInForce": time_in_force
        }

        result = self._request("POST", "/fapi/v1/order", params=params, signed=True)

        logger.info(
            f"Limit order created: {symbol} {side} {quantity} @ {price} "
            f"(orderId: {result['orderId']})"
        )

        return {
            "order_id": result["orderId"],
            "symbol": result["symbol"],
            "side": result["side"],
            "type": result["type"],
            "quantity": float(result["origQty"]),
            "price": float(result["price"]),
            "status": result["status"],
            "timestamp": result["updateTime"]
        }

    def create_stop_loss(
        self,
        symbol: str,
        side: str,  # BUY or SELL (포지션 반대)
        quantity: float,
        stop_price: float
    ) -> Dict[str, Any]:
        """Stop Loss 주문"""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "STOP_MARKET",
            "stopPrice": stop_price,
            "quantity": quantity,
            "closePosition": "false"
        }

        result = self._request("POST", "/fapi/v1/order", params=params, signed=True)

        logger.info(
            f"Stop Loss created: {symbol} {side} {quantity} @ {stop_price} "
            f"(orderId: {result['orderId']})"
        )

        return {
            "order_id": result["orderId"],
            "symbol": result["symbol"],
            "side": result["side"],
            "type": result["type"],
            "stop_price": float(result["stopPrice"]),
            "status": result["status"]
        }

    def create_take_profit(
        self,
        symbol: str,
        side: str,  # BUY or SELL (포지션 반대)
        quantity: float,
        take_profit_price: float
    ) -> Dict[str, Any]:
        """Take Profit 주문"""
        params = {
            "symbol": symbol,
            "side": side,
            "type": "TAKE_PROFIT_MARKET",
            "stopPrice": take_profit_price,
            "quantity": quantity,
            "closePosition": "false"
        }

        result = self._request("POST", "/fapi/v1/order", params=params, signed=True)

        logger.info(
            f"Take Profit created: {symbol} {side} {quantity} @ {take_profit_price} "
            f"(orderId: {result['orderId']})"
        )

        return {
            "order_id": result["orderId"],
            "symbol": result["symbol"],
            "side": result["side"],
            "type": result["type"],
            "stop_price": float(result["stopPrice"]),
            "status": result["status"]
        }

    def close_position(self, symbol: str) -> Dict[str, Any]:
        """포지션 전체 청산"""
        # 현재 포지션 조회
        positions = self.get_positions(symbol=symbol)

        if not positions:
            return {
                "success": False,
                "message": f"No open position for {symbol}"
            }

        position = positions[0]
        position_amt = position["position_amt"]

        # 포지션 반대 방향으로 시장가 주문
        if position_amt > 0:
            # LONG 포지션 → SELL
            side = "SELL"
        else:
            # SHORT 포지션 → BUY
            side = "BUY"
            position_amt = abs(position_amt)

        result = self.create_market_order(
            symbol=symbol,
            side=side,
            quantity=position_amt,
            reduce_only=True
        )

        logger.info(f"Position closed: {symbol}")

        return {
            "success": True,
            "message": f"Position closed for {symbol}",
            "order": result
        }

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """주문 취소"""
        params = {
            "symbol": symbol,
            "orderId": order_id
        }

        result = self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

        logger.info(f"Order cancelled: {symbol} orderId={order_id}")

        return {
            "order_id": result["orderId"],
            "symbol": result["symbol"],
            "status": result["status"]
        }

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """미체결 주문 조회"""
        params = {}
        if symbol:
            params["symbol"] = symbol

        result = self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

        return [
            {
                "order_id": order["orderId"],
                "symbol": order["symbol"],
                "side": order["side"],
                "type": order["type"],
                "price": float(order["price"]) if order["price"] else None,
                "quantity": float(order["origQty"]),
                "status": order["status"],
                "timestamp": order["time"]
            }
            for order in result
        ]

    def get_current_price(self, symbol: str) -> float:
        """현재 시장가 조회"""
        result = self._request("GET", f"/fapi/v1/ticker/price", params={"symbol": symbol})
        return float(result["price"])
