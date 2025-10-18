"""
Centralized Logging Configuration

Features:
- Structured JSON logging
- Request/Response logging
- Security event logging
- Error tracking with stack traces
- Performance monitoring
"""

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime
from pathlib import Path

# 로그 디렉토리 생성
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """JSON 구조화 로그 포맷터"""

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON으로 변환"""

        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 추가 컨텍스트 정보
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "account_id"):
            log_data["account_id"] = record.account_id
        if hasattr(record, "exchange"):
            log_data["exchange"] = record.exchange
        if hasattr(record, "symbol"):
            log_data["symbol"] = record.symbol
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # 예외 정보
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 스택 트레이스
        if record.stack_info:
            log_data["stack_trace"] = self.formatStack(record.stack_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(log_level: str = "INFO"):
    """중앙화된 로깅 설정"""

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 콘솔 핸들러 (개발 환경)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 - 일반 로그 (JSON 구조화)
    file_handler = logging.FileHandler(
        LOG_DIR / "app.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    # 파일 핸들러 - 에러 로그
    error_handler = logging.FileHandler(
        LOG_DIR / "error.log",
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)

    # 파일 핸들러 - 보안 이벤트 로그
    security_handler = logging.FileHandler(
        LOG_DIR / "security.log",
        encoding='utf-8'
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(StructuredFormatter())

    # 보안 로거 별도 설정
    security_logger = logging.getLogger("security")
    security_logger.addHandler(security_handler)

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    logging.info("Logging system initialized")


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 가져오기"""
    return logging.getLogger(name)


def log_security_event(
    event_type: str,
    user_id: str = None,
    account_id: str = None,
    ip_address: str = None,
    details: Dict[str, Any] = None
):
    """보안 이벤트 로깅"""
    security_logger = logging.getLogger("security")

    log_record = security_logger.makeRecord(
        name="security",
        level=logging.WARNING,
        fn="",
        lno=0,
        msg=f"Security event: {event_type}",
        args=(),
        exc_info=None
    )

    # 추가 컨텍스트
    log_record.event_type = event_type
    if user_id:
        log_record.user_id = user_id
    if account_id:
        log_record.account_id = account_id
    if ip_address:
        log_record.ip_address = ip_address
    if details:
        log_record.details = json.dumps(details)

    security_logger.handle(log_record)


def log_api_request(
    method: str,
    path: str,
    user_id: str = None,
    status_code: int = None,
    duration_ms: float = None,
    error: str = None
):
    """API 요청 로깅"""
    logger = logging.getLogger("api")

    message = f"{method} {path}"
    if status_code:
        message += f" - {status_code}"
    if duration_ms:
        message += f" ({duration_ms:.2f}ms)"
    if error:
        message += f" - ERROR: {error}"

    log_level = logging.ERROR if error else logging.INFO

    log_record = logger.makeRecord(
        name="api",
        level=log_level,
        fn="",
        lno=0,
        msg=message,
        args=(),
        exc_info=None
    )

    log_record.method = method
    log_record.path = path
    if user_id:
        log_record.user_id = user_id
    if status_code:
        log_record.status_code = status_code
    if duration_ms:
        log_record.duration_ms = duration_ms

    logger.handle(log_record)
