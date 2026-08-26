import os
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ReviveAI"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./reviveai.db"
    
    # Razorpay Test Mode Credentials
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: str = "test_webhook_secret_reviveai"
    
    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Policy Guardrail Defaults
    MAX_RETRIES_PER_CASE: int = 3
    MIN_HOURS_BETWEEN_RETRIES: int = 24
    AUTONOMOUS_AMOUNT_LIMIT_INR: float = 50000.0
    MIN_CONFIDENCE_THRESHOLD: float = 0.65
    MAX_CONTACT_ATTEMPTS: int = 2
    
    # Cost & Friction Parameters for Value Calculation (INR)
    COST_PER_RETRY_INR: float = 5.0
    COST_PER_EMAIL_INR: float = 0.5
    COST_PER_WHATSAPP_INR: float = 2.5
    COST_HUMAN_REVIEW_INR: float = 150.0
    
    # Friction Penalty Multipliers (loss of customer goodwill)
    FRICTION_PENALTY_RETRY: float = 10.0
    FRICTION_PENALTY_EMAIL: float = 20.0
    FRICTION_PENALTY_WHATSAPP: float = 60.0
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("RAZORPAY_KEY_ID")
    @classmethod
    def validate_test_mode_only(cls, v: Optional[str]) -> Optional[str]:
        if v and v.startswith("rzp_live_"):
            raise ValueError(
                "CRITICAL SECURITY VIOLATION: Live Razorpay credentials detected (rzp_live_...). "
                "ReviveAI strictly operates in TEST MODE only to guarantee financial safety. "
                "Please provide a key starting with 'rzp_test_'."
            )
        return v

    @property
    def is_razorpay_configured(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET and self.RAZORPAY_KEY_ID.startswith("rzp_test_"))

    @property
    def is_gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY and len(self.GEMINI_API_KEY.strip()) > 0)


settings = Settings()
