"""
Custom Exceptions and Error Handlers

Features:
- Custom exception types
- Centralized error handling
- Consistent error responses
- Security-aware error messages (no sensitive data leakage)
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ==================== Custom Exceptions ====================

class TradingBotException(Exception):
    """Base exception for TradingBot"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(TradingBotException):
    """인증 실패"""

    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class AuthorizationError(TradingBotException):
    """권한 부족"""

    def __init__(self, message: str = "Insufficient permissions", details: Dict[str, Any] = None):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class ValidationError(TradingBotException):
    """입력 검증 실패"""

    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        if field:
            details = details or {}
            details["field"] = field
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class ExchangeAPIError(TradingBotException):
    """거래소 API 에러"""

    def __init__(self, message: str, exchange: str, error_code: str = None, details: Dict[str, Any] = None):
        details = details or {}
        details["exchange"] = exchange
        if error_code:
            details["error_code"] = error_code
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY, details=details)


class OrderExecutionError(TradingBotException):
    """주문 실행 실패"""

    def __init__(self, message: str, order_type: str = None, symbol: str = None, details: Dict[str, Any] = None):
        details = details or {}
        if order_type:
            details["order_type"] = order_type
        if symbol:
            details["symbol"] = symbol
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


class InsufficientBalanceError(TradingBotException):
    """잔액 부족"""

    def __init__(self, message: str = "Insufficient balance", required: float = None, available: float = None):
        details = {}
        if required:
            details["required"] = required
        if available:
            details["available"] = available
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class RateLimitExceeded(TradingBotException):
    """API 속도 제한 초과"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(message, status_code=status.HTTP_429_TOO_MANY_REQUESTS, details=details)


class EncryptionError(TradingBotException):
    """암호화/복호화 실패"""

    def __init__(self, message: str = "Encryption/Decryption failed"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountNotFoundError(TradingBotException):
    """계정을 찾을 수 없음"""

    def __init__(self, account_id: str):
        super().__init__(
            f"Account not found: {account_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"account_id": account_id}
        )


# ==================== Error Response Formatter ====================

def create_error_response(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """표준 에러 응답 생성"""

    response = {
        "success": False,
        "error": {
            "code": status_code,
            "message": message
        }
    }

    if details:
        response["error"]["details"] = details

    if request_id:
        response["request_id"] = request_id

    return response


# ==================== Global Exception Handlers ====================

async def tradingbot_exception_handler(request: Request, exc: TradingBotException):
    """TradingBot 커스텀 예외 핸들러"""

    logger.error(
        f"TradingBot exception: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            details=exc.details
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """FastAPI HTTP 예외 핸들러"""

    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic 입력 검증 예외 핸들러"""

    errors = exc.errors()

    logger.warning(
        f"Validation error: {errors}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors
        }
    )

    # 사용자 친화적 에러 메시지 생성
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Invalid input data",
            details={
                "validation_errors": error_messages,
                "raw_errors": errors
            }
        )
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러 (최후의 방어선)"""

    logger.critical(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )

    # 프로덕션 환경에서는 상세 에러 정보를 숨김
    from app.core.config import settings

    if settings.DEBUG:
        error_detail = str(exc)
    else:
        error_detail = "Internal server error"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=error_detail
        )
    )


# ==================== Exception Handler Registration ====================

def register_exception_handlers(app):
    """FastAPI 앱에 예외 핸들러 등록"""

    app.add_exception_handler(TradingBotException, tradingbot_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
