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

from app.core.stability import with_retry, RetryStrategy

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
        """
        계좌 잔액 조회 (ALL Account Types)

        OKX 계정 구조:
        - Funding Account: 입출금 계정 (Deposit/Withdraw)
        - Trading Account: 거래 계정 (Futures, Margin, etc)
        - Note: Spot trading uses Trading Account
        """
        # 1. Trading Account 조회
        trading_result = self._request("GET", "/api/v5/account/balance")

        # 2. Funding Account 조회
        try:
            funding_result = self._request("GET", "/api/v5/asset/balances")
        except Exception as e:
            logger.warning(f"Failed to fetch funding balance: {e}")
            funding_result = []

        # 3. Trading Account - USDT 잔액 추출
        trading_usdt = {"availBal": "0", "eq": "0"}
        if trading_result:
            details = trading_result[0].get("details", [])
            trading_usdt = next(
                (item for item in details if item["ccy"] == "USDT"),
                trading_usdt
            )

        # 4. Funding Account - USDT 잔액 추출
        funding_usdt = {"availBal": "0", "bal": "0"}
        if funding_result:
            funding_usdt = next(
                (item for item in funding_result if item["ccy"] == "USDT"),
                funding_usdt
            )

        # 5. Sum both accounts for total balance
        total_available = float(trading_usdt["availBal"]) + float(funding_usdt["availBal"])
        total_balance_combined = float(trading_usdt["eq"]) + float(funding_usdt.get("bal", "0"))

        # 6. All assets with balance > 0 (Trading Account)
        all_trading_assets = []
        if trading_result:
            all_trading_assets = [
                {
                    "asset": detail["ccy"],
                    "available_balance": float(detail["availBal"]),
                    "total_balance": float(detail["eq"]),
                    "account_type": "trading"
                }
                for detail in trading_result[0].get("details", [])
                if float(detail["eq"]) > 0
            ]

        # 7. All assets with balance > 0 (Funding Account)
        all_funding_assets = []
        if funding_result:
            all_funding_assets = [
                {
                    "asset": item["ccy"],
                    "available_balance": float(item["availBal"]),
                    "total_balance": float(item["bal"]),
                    "account_type": "funding"
                }
                for item in funding_result
                if float(item["bal"]) > 0
            ]

        return {
            "asset": "USDT",
            "available_balance": str(total_available),
            "total_balance": str(total_balance_combined),
            "account_structure": {
                "funding": {
                    "usdt_available": float(funding_usdt["availBal"]),
                    "usdt_total": float(funding_usdt.get("bal", "0"))
                },
                "trading": {
                    "usdt_available": float(trading_usdt["availBal"]),
                    "usdt_total": float(trading_usdt["eq"])
                }
            },
            "all_assets": all_trading_assets + all_funding_assets
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

    def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """24시간 통계 조회"""
        result = self._request("GET", "/api/v5/market/ticker", params={"instId": symbol})

        if not result:
            raise Exception(f"Failed to get 24h ticker for {symbol}")

        ticker = result[0]

        return {
            "symbol": ticker["instId"],
            "price_change": float(ticker["last"]) - float(ticker["open24h"]),
            "price_change_percent": ((float(ticker["last"]) - float(ticker["open24h"])) / float(ticker["open24h"]) * 100) if float(ticker["open24h"]) > 0 else 0,
            "last_price": float(ticker["last"]),
            "high_price": float(ticker["high24h"]),
            "low_price": float(ticker["low24h"]),
            "volume": float(ticker["vol24h"]),
            "quote_volume": float(ticker["volCcy24h"]),
            "open_time": int(ticker["ts"]) - (24 * 60 * 60 * 1000),  # 24시간 전
            "close_time": int(ticker["ts"]),
            "count": 0  # OKX는 거래 횟수 제공 안함
        }

    def transfer_asset(
        self,
        currency: str,
        amount: float,
        from_account: str,  # "6" (Funding) or "18" (Trading)
        to_account: str      # "6" (Funding) or "18" (Trading)
    ) -> Dict[str, Any]:
        """
        계정 간 자산 이동 (Funding ↔ Trading)

        OKX 계정 타입 코드:
        - "6": Funding account (입출금 계정)
        - "18": Trading account (거래 계정)

        Args:
            currency: 자산 코드 (e.g., "USDT", "BTC")
            amount: 이동할 수량
            from_account: 출금 계정 ("6" or "18")
            to_account: 입금 계정 ("6" or "18")

        Returns:
            이동 결과
        """
        body = {
            "ccy": currency,
            "amt": str(amount),
            "from": from_account,
            "to": to_account,
            "type": "0"  # Internal transfer
        }

        result = self._request("POST", "/api/v5/asset/transfer", body=body)

        if not result:
            raise Exception("Transfer failed")

        transfer_data = result[0]

        logger.info(
            f"Asset transferred: {amount} {currency} from {from_account} to {to_account} "
            f"(transId: {transfer_data.get('transId', 'N/A')})"
        )

        return {
            "success": True,
            "transfer_id": transfer_data.get("transId"),
            "currency": currency,
            "amount": amount,
            "from_account": "funding" if from_account == "6" else "trading",
            "to_account": "funding" if to_account == "6" else "trading",
            "message": f"Transferred {amount} {currency}"
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
