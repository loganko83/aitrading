from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os


# Determine which .env file to load based on ENVIRONMENT variable
_environment = os.getenv("ENVIRONMENT", "development")
_env_file = f".env.{_environment}"

# Fall back to .env if environment-specific file doesn't exist
if not os.path.exists(_env_file):
    _env_file = ".env"

print(f"🔧 Loading configuration from: {_env_file}")


class Settings(BaseSettings):
    """Application configuration settings with environment support"""

    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

    # Application
    APP_NAME: str = "TradingBot AI Backend"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production

    # Database
    DATABASE_URL: str

    # Binance API
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    BINANCE_TESTNET: bool = True

    # OKX API
    OKX_API_KEY: str = ""
    OKX_API_SECRET: str = ""
    OKX_PASSPHRASE: str = ""
    OKX_TESTNET: bool = True

    # AI APIs
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    WEBHOOK_SECRET: str  # TradingView webhook verification key
    ENCRYPTION_KEY: Optional[str] = None  # API key encryption (Fernet key)
    ENCRYPTION_SALT: Optional[str] = None  # Salt for key derivation (base64-encoded)

    # Trading Parameters
    DEFAULT_LEVERAGE: int = 3
    MAX_POSITION_SIZE_PCT: float = 0.10
    ATR_PERIOD: int = 14

    # AI Ensemble Weights
    ML_WEIGHT: float = 0.40
    GPT4_WEIGHT: float = 0.25
    LLAMA_WEIGHT: float = 0.25
    TA_WEIGHT: float = 0.10

    # Entry/Exit Thresholds
    MIN_PROBABILITY: float = 0.80
    MIN_CONFIDENCE: float = 0.70
    MIN_AGREEMENT: float = 0.70

    # Logging
    LOG_LEVEL: str = "INFO"

    # Security Settings (Production)
    ALLOWED_HOSTS: Optional[List[str]] = None
    ENABLE_HTTPS_REDIRECT: bool = False
    ENABLE_CORS: bool = True

    # CORS Origins (Docker-compatible: comma-separated string from env)
    # Example: CORS_ORIGINS="http://localhost:3000,http://localhost:3001,https://your-domain.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = False

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None  # 텔레그램 봇 토큰 (@BotFather에서 발급)

    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.ENVIRONMENT == "development"

    def validate_production_settings(self):
        """프로덕션 환경 설정 검증"""
        if not self.is_production:
            return

        errors = []

        # 프로덕션에서는 DEBUG 모드 비활성화 필수
        if self.DEBUG:
            errors.append("DEBUG must be False in production")

        # 프로덕션에서는 기본 시크릿 키 사용 불가
        if "generate" in self.SECRET_KEY.lower() or "your" in self.SECRET_KEY.lower():
            errors.append("SECRET_KEY must be a secure generated key in production")

        if "generate" in self.WEBHOOK_SECRET.lower() or "your" in self.WEBHOOK_SECRET.lower():
            errors.append("WEBHOOK_SECRET must be a secure generated key in production")

        # 프로덕션에서는 ENCRYPTION_KEY 필수
        if not self.ENCRYPTION_KEY or "generate" in self.ENCRYPTION_KEY.lower():
            errors.append("ENCRYPTION_KEY must be set and secure in production")

        # ENCRYPTION_KEY가 없을 때 ENCRYPTION_SALT는 필수
        if not self.ENCRYPTION_KEY and (not self.ENCRYPTION_SALT or "generate" in self.ENCRYPTION_SALT.lower()):
            errors.append("ENCRYPTION_SALT must be set when ENCRYPTION_KEY is not provided in production")

        # 프로덕션에서는 테스트넷 사용 불가 (경고만)
        if self.BINANCE_TESTNET:
            print("⚠️  WARNING: BINANCE_TESTNET is True in production - ensure this is intentional")

        if self.OKX_TESTNET:
            print("⚠️  WARNING: OKX_TESTNET is True in production - ensure this is intentional")

        if errors:
            raise ValueError(f"Production configuration errors: {', '.join(errors)}")


def get_settings() -> Settings:
    """설정 객체 생성 및 검증"""
    settings = Settings()

    # 프로덕션 환경 설정 검증
    if settings.is_production:
        settings.validate_production_settings()
        print("✅ Production configuration validated")

    return settings


settings = get_settings()
