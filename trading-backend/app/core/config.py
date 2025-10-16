from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""

    # Application
    APP_NAME: str = "TradingBot AI Backend"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Binance API
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    BINANCE_TESTNET: bool = True

    # AI APIs
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
