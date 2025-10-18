"""
OKX Futures API 클라이언트

Features:
- 시장가/지정가 주문
- 포지션 관리
- 레버리지 설정
- Stop Loss / Take Profit
"""

from typing import Dict, Any, Optional, List
import hmac
import hashlib
import base64
import time
import requests
from datetime import datetime
import logging

from app.core.stability import with_retry, with_timeout, RetryStrategy

logger = logging.getLogger(__name__)


class OKXClient:
    """OKX Futures API 클라이언트"""

    def __init__(self, api_key: str, api_secret: str, passphrase: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.testnet = testnet

        # API URLs
        if testnet:
            self.base_url = "https://www.okx.com"  # OKX는 별도 테스트넷 URL 없음 (시뮬레이션 계정 사용)
        else:
            self.base_url = "https://www.okx.com"

    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """HMAC SHA256 서명 생성"""
        message = timestamp + method + request_path + body
        mac = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        )
        signature = base64.b64encode(mac.digest()).decode("utf-8")
        return signature

    def _get_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        """API 요청 헤더 생성"""
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        signature = self._generate_signature(timestamp, method, request_path, body)

        return {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

    @with_retry(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
    @with_timeout(timeout_seconds=10.0)
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """API 요청"""
        url = f"{self.base_url}{endpoint}"

        # Body JSON 문자열
        body_str = ""
        if body:
            import json
            body_str = json.dumps(body)

        # 헤더 생성
        headers = self._get_headers(method, endpoint, body_str)

        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, data=body_str, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            result = response.json()

            # OKX는 항상 {"code": "0", "msg": "", "data": [...]} 형식
            if result.get("code") != "0":
                raise Exception(f"OKX API error: {result.get('msg', 'Unknown error')}")

            return result.get("data", [])

        except requests.exceptions.RequestException as e:
            logger.error(f"OKX API request failed: {str(e)}")
            raise

    def get_account_balance(self) -> Dict[str, Any]:
        """계좌 잔액 조회"""
        result = self._request("GET", "/api/v5/account/balance")

        if not result:
            return {
                "asset": "USDT",
                "available_balance": 0.0,
                "total_balance": 0.0
            }

        # USDT 잔액 추출
        details = result[0].get("details", [])
        usdt_detail = next(
            (item for item in details if item["ccy"] == "USDT"),
            {"availBal": "0", "eq": "0"}
        )

        return {
            "asset": "USDT",
            "available_balance": float(usdt_detail["availBal"]),
            "total_balance": float(usdt_detail["eq"])
        }

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """포지션 조회"""
        params = {}
        if symbol:
            # OKX 형식: BTC-USDT-SWAP
            params["instId"] = symbol

        result = self._request("GET", "/api/v5/account/positions", params=params)

        active_positions = [
            {
                "symbol": pos["instId"],
                "position_amt": float(pos["pos"]),
                "entry_price": float(pos["avgPx"]),
                "unrealized_pnl": float(pos["upl"]),
                "leverage": int(float(pos["lever"])),
                "side": pos["posSide"]  # long or short
            }
            for pos in result
            if float(pos["pos"]) != 0
        ]

        return active_positions

    def set_leverage(self, symbol: str, leverage: int, margin_mode: str = "cross") -> Dict[str, Any]:
        """레버리지 설정"""
        body = {
            "instId": symbol,
            "lever": str(leverage),
            "mgnMode": margin_mode  # cross or isolated
        }

        result = self._request("POST", "/api/v5/account/set-leverage", body=body)

        logger.info(f"Leverage set: {symbol} = {leverage}x ({margin_mode})")

        return {
            "symbol": symbol,
            "leverage": leverage,
            "margin_mode": margin_mode
        }

    def create_market_order(
        self,
        symbol: str,
        side: str,  # buy or sell
        quantity: float,
        position_side: str = "net"  # net, long, short
    ) -> Dict[str, Any]:
        """시장가 주문"""
        body = {
            "instId": symbol,
            "tdMode": "cross",  # cross margin
            "side": side.lower(),
            "ordType": "market",
            "sz": str(quantity),
            "posSide": position_side
        }

        result = self._request("POST", "/api/v5/trade/order", body=body)

        if not result:
            raise Exception("Order creation failed")

        order_data = result[0]

        logger.info(
            f"Market order created: {symbol} {side} {quantity} "
            f"(orderId: {order_data['ordId']})"
        )

        return {
            "order_id": order_data["ordId"],
            "symbol": symbol,
            "side": side,
            "type": "market",
            "quantity": quantity,
            "status": order_data["sCode"]  # Success code
        }

    def create_limit_order(
        self,
        symbol: str,
        side: str,  # buy or sell
        quantity: float,
        price: float,
        position_side: str = "net"
    ) -> Dict[str, Any]:
        """지정가 주문"""
        body = {
            "instId": symbol,
            "tdMode": "cross",
            "side": side.lower(),
            "ordType": "limit",
            "sz": str(quantity),
            "px": str(price),
            "posSide": position_side
        }

        result = self._request("POST", "/api/v5/trade/order", body=body)

        if not result:
            raise Exception("Order creation failed")

        order_data = result[0]

        logger.info(
            f"Limit order created: {symbol} {side} {quantity} @ {price} "
            f"(orderId: {order_data['ordId']})"
        )

        return {
            "order_id": order_data["ordId"],
            "symbol": symbol,
            "side": side,
            "type": "limit",
            "quantity": quantity,
            "price": price,
            "status": order_data["sCode"]
        }

    def close_position(self, symbol: str, position_side: str = "net") -> Dict[str, Any]:
        """포지션 전체 청산"""
        # 현재 포지션 조회
        positions = self.get_positions(symbol=symbol)

        if not positions:
            return {
                "success": False,
                "message": f"No open position for {symbol}"
            }

        position = positions[0]
        position_amt = abs(position["position_amt"])

        # 포지션 반대 방향으로 시장가 주문
        if position["side"] == "long":
            side = "sell"
        else:
            side = "buy"

        body = {
            "instId": symbol,
            "mgnMode": "cross",
            "posSide": position_side,
            "cxlOnClosePos": "true"  # 포지션 청산 시 미체결 주문 자동 취소
        }

        result = self._request("POST", "/api/v5/trade/close-position", body=body)

        logger.info(f"Position closed: {symbol}")

        return {
            "success": True,
            "message": f"Position closed for {symbol}",
            "result": result
        }

    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """주문 취소"""
        body = {
            "instId": symbol,
            "ordId": order_id
        }

        result = self._request("POST", "/api/v5/trade/cancel-order", body=body)

        logger.info(f"Order cancelled: {symbol} orderId={order_id}")

        return {
            "order_id": order_id,
            "symbol": symbol,
            "status": "cancelled"
        }

    def get_current_price(self, symbol: str) -> float:
        """현재 시장가 조회"""
        result = self._request("GET", f"/api/v5/market/ticker", params={"instId": symbol})

        if not result:
            raise Exception(f"Failed to get price for {symbol}")

        return float(result[0]["last"])

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
            # OKX API 에러 메시지 파싱
            error_message = str(e)
            if "Incorrect API key" in error_message or "Invalid API key" in error_message:
                return {
                    "valid": False,
                    "message": "Invalid API key"
                }
            elif "Invalid Sign" in error_message or "Invalid signature" in error_message:
                return {
                    "valid": False,
                    "message": "Invalid API secret or signature"
                }
            elif "Passphrase" in error_message:
                return {
                    "valid": False,
                    "message": "Invalid passphrase"
                }
            else:
                return {
                    "valid": False,
                    "message": f"Validation error: {error_message}"
                }
