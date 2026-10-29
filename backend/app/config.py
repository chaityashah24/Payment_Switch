import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Secure Payment Switch & Merchant Acquiring Simulator"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./paymentswitch.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-lntfintech-switch-secret-key-32-chars-min-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    COOKIE_NAME: str = "switch_access_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Simulator defaults
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_SETTLEMENT_CUTOFF_HOUR_UTC: int = 18  # 18:00 UTC = 23:30 IST
    MAX_PAYMENT_AMOUNT_PAISE: int = 100000000  # ₹10,00,000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
