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
from app.core.stability import with_retry, RetryStrategy

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
            self.spot_base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://fapi.binance.com"
            self.spot_base_url = "https://api.binance.com"

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
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
        use_spot_url: bool = False  # NEW: Spot/Funding API용
    ) -> Dict[str, Any]:
        """API 요청"""
        # Spot/Funding API는 spot_base_url 사용
        base = self.spot_base_url if use_spot_url else self.base_url
        url = f"{base}{endpoint}"

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
        """
        계좌 잔액 조회 (ALL Account Types)

        Binance 계정 구조:
        - Futures Account: 선물 거래 계정
        - Spot Account: 현물 거래 계정
        - Funding Wallet: 입출금 지갑 (NEW)
        """
        # 1. Futures Account 조회
        futures_balance = self._request("GET", "/fapi/v2/balance", signed=True)
        futures_usdt = next(
            (item for item in futures_balance if item["asset"] == "USDT"),
            {"availableBalance": "0", "balance": "0"}
        )

        # 2. Spot Account 조회
        try:
            spot_account = self._request("GET", "/api/v3/account", signed=True, use_spot_url=True)
            spot_balances = spot_account.get("balances", [])
            spot_usdt = next(
                (item for item in spot_balances if item["asset"] == "USDT"),
                {"free": "0", "locked": "0"}
            )
            spot_usdt_total = float(spot_usdt["free"]) + float(spot_usdt["locked"])
        except Exception as e:
            logger.warning(f"Failed to fetch Spot balance: {e}")
            spot_usdt = {"free": "0", "locked": "0"}
            spot_usdt_total = 0.0
            spot_balances = []

        # 3. Funding Wallet 조회 (NEW)
        try:
            funding_assets = self._request("GET", "/sapi/v1/asset/get-funding-asset", signed=True, use_spot_url=True)
            funding_usdt = next(
                (item for item in funding_assets if item["asset"] == "USDT"),
                {"free": "0", "locked": "0", "freeze": "0"}
            )
            # Funding Wallet: free + locked + freeze
            funding_usdt_available = float(funding_usdt.get("free", "0"))
            funding_usdt_total = (
                float(funding_usdt.get("free", "0")) +
                float(funding_usdt.get("locked", "0")) +
                float(funding_usdt.get("freeze", "0"))
            )
        except Exception as e:
            logger.warning(f"Failed to fetch Funding Wallet balance: {e}")
            funding_usdt_available = 0.0
            funding_usdt_total = 0.0
            funding_assets = []

        # 4. Total USDT across all accounts (Futures + Spot + Funding)
        total_available = (
            float(futures_usdt["availableBalance"]) +
            float(spot_usdt["free"]) +
            funding_usdt_available
        )
        total_balance = (
            float(futures_usdt["balance"]) +
            spot_usdt_total +
            funding_usdt_total
        )

        # 5. All assets with balance > 0 (Futures)
        all_futures_assets = [
            {
                "asset": item["asset"],
                "available_balance": float(item["availableBalance"]),
                "total_balance": float(item["balance"]),
                "account_type": "futures"
            }
            for item in futures_balance
            if float(item["balance"]) > 0
        ]

        # 6. All assets with balance > 0 (Spot)
        all_spot_assets = [
            {
                "asset": item["asset"],
                "available_balance": float(item["free"]),
                "total_balance": float(item["free"]) + float(item["locked"]),
                "account_type": "spot"
            }
            for item in spot_balances
            if (float(item["free"]) + float(item["locked"])) > 0
        ]

        # 7. All assets with balance > 0 (Funding)
        all_funding_assets = [
            {
                "asset": item["asset"],
                "available_balance": float(item.get("free", "0")),
                "total_balance": (
                    float(item.get("free", "0")) +
                    float(item.get("locked", "0")) +
                    float(item.get("freeze", "0"))
                ),
                "account_type": "funding"
            }
            for item in funding_assets
            if (float(item.get("free", "0")) + float(item.get("locked", "0")) + float(item.get("freeze", "0"))) > 0
        ]

        return {
            "asset": "USDT",
            "available_balance": str(total_available),
            "total_balance": str(total_balance),
            "account_structure": {
                "futures": {
                    "usdt_available": float(futures_usdt["availableBalance"]),
                    "usdt_total": float(futures_usdt["balance"])
                },
                "spot": {
                    "usdt_available": float(spot_usdt["free"]),
                    "usdt_total": spot_usdt_total
                },
                "funding": {  # NEW
                    "usdt_available": funding_usdt_available,
                    "usdt_total": funding_usdt_total
                }
            },
            "all_assets": all_futures_assets + all_spot_assets + all_funding_assets
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

    def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """24시간 통계 조회"""
        result = self._request("GET", "/fapi/v1/ticker/24hr", params={"symbol": symbol})

        return {
            "symbol": result["symbol"],
            "price_change": float(result["priceChange"]),
            "price_change_percent": float(result["priceChangePercent"]),
            "last_price": float(result["lastPrice"]),
            "high_price": float(result["highPrice"]),
            "low_price": float(result["lowPrice"]),
            "volume": float(result["volume"]),
            "quote_volume": float(result["quoteVolume"]),
            "open_time": result["openTime"],
            "close_time": result["closeTime"],
            "count": result["count"]  # 거래 횟수
        }

    def validate_credentials(self) -> Dict[str, Any]:
        """
        API 키 유효성 검증

        Returns:
            Dict with validation result:
            - valid: bool
            - message: str
            - details: Optional[Dict] (account info if valid)

        Raises:
            Exception: API 호출 실패 시
        """
        try:
            # 계정 잔액 조회를 통해 API 키 유효성 검증
            account_info = self.get_account_balance()

            return {
                "valid": True,
                "message": "API credentials are valid",
                "details": {
                    "available_balance": account_info["available_balance"],
                    "total_balance": account_info["total_balance"],
                    "testnet": self.testnet
                }
            }

        except requests.exceptions.HTTPError as e:
            # HTTP 에러 처리
            if e.response.status_code == 401:
                return {
                    "valid": False,
                    "message": "Invalid API key or signature",
                    "error_code": 401
                }
            elif e.response.status_code == 403:
                return {
                    "valid": False,
                    "message": "API key does not have required permissions",
                    "error_code": 403
                }
            else:
                return {
                    "valid": False,
                    "message": f"API validation failed: {str(e)}",
                    "error_code": e.response.status_code
                }

        except Exception as e:
            logger.error(f"Credential validation error: {str(e)}")
            return {
                "valid": False,
                "message": f"Validation error: {str(e)}"
            }

    def transfer_asset(self, from_account: str, to_account: str, asset: str, amount: float) -> Dict[str, Any]:
        """
        계정 간 자산 이동

        Args:
            from_account: 출금 계정 ('SPOT' or 'FUTURES')
            to_account: 입금 계정 ('SPOT' or 'FUTURES')
            asset: 자산 심볼 (e.g., 'USDT')
            amount: 이동 금액

        Returns:
            Dict with transfer result:
            - success: bool
            - tranId: transfer transaction ID
            - amount: transferred amount
            - from_account: source account
            - to_account: destination account

        Raises:
            ValueError: Invalid account type or insufficient balance
            Exception: API call failed
        """
        # 계정 타입 매핑
        transfer_types = {
            ('SPOT', 'FUTURES'): 'MAIN_UMFUTURE',
            ('FUTURES', 'SPOT'): 'UMFUTURE_MAIN'
        }

        transfer_key = (from_account.upper(), to_account.upper())
        if transfer_key not in transfer_types:
            raise ValueError(f"Invalid transfer direction: {from_account} -> {to_account}. Only SPOT <-> FUTURES supported.")

        transfer_type = transfer_types[transfer_key]

        # API 호출
        params = {
            "type": transfer_type,
            "asset": asset.upper(),
            "amount": str(amount)
        }

        try:
            result = self._request("POST", "/sapi/v1/asset/transfer", params=params, signed=True)

            logger.info(f"Binance transfer successful: {amount} {asset} from {from_account} to {to_account}")

            return {
                "success": True,
                "tranId": result["tranId"],
                "amount": amount,
                "asset": asset,
                "from_account": from_account,
                "to_account": to_account,
                "timestamp": result.get("timestamp", int(time.time() * 1000))
            }

        except requests.exceptions.HTTPError as e:
            error_msg = f"Binance transfer failed: {str(e)}"
            logger.error(error_msg)

            # Parse error response
            try:
                error_data = e.response.json()
                error_code = error_data.get("code")
                error_message = error_data.get("msg", str(e))

                # Common error codes
                if error_code == -4046:
                    raise ValueError(f"Insufficient balance in {from_account} account")
                elif error_code == -1003:
                    raise ValueError("Transfer amount too small or too large")
                else:
                    raise Exception(f"Transfer failed: {error_message}")
            except:
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"Unexpected transfer error: {str(e)}")
            raise
