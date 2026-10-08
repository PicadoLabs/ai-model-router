from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    DATABASE_URL: str = "sqlite+aiosqlite:///./model_router.db"
    REDIS_URL: Optional[str] = None
    ROUTER_ANALYZER: str = "rules"  # "rules" or "llm"
    DEFAULT_ROUTING_POLICY: str = "balanced"
    BASELINE_MODEL_ID: str = "mock-power"

    DEFAULT_PROVIDER: str = "mock"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # External Provider Keys (optional)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    TOGETHER_API_KEY: Optional[str] = None

    # Budgets
    DAILY_BUDGET: float = 10.00
    MONTHLY_BUDGET: float = 100.00
    PER_REQUEST_BUDGET: float = 1.00

    # Execution / Reliability
    MAX_RETRIES: int = 2
    PROVIDER_TIMEOUT_SECONDS: float = 30.0

    # Authentication & Rate Limiting
    AUTH_REQUIRED: bool = False
    DEFAULT_RATE_LIMIT_RPM: int = 120
    DEFAULT_RATE_LIMIT_TPM: int = 200000

    # Reinforcement Learning / Thompson Sampling
    RL_ROUTING_ENABLED: bool = True
    RL_EXPLORATION_RATE: float = 0.15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
