"""
SALF Backend Configuration
Secure Academic Ledger Framework - Core Settings
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application
    APP_NAME: str = "SALF - Secure Academic Ledger Framework"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./salf.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Blockchain - Hyperledger Besu
    BESU_RPC_URL: str = "http://127.0.0.1:8545"
    BESU_CHAIN_ID: int = 1337
    BESU_PRIVATE_KEY: Optional[str] = None
    
    # Contract Addresses (populated after deployment)
    ACCESS_CONTROL_ADDRESS: Optional[str] = None
    ACADEMIC_CREDIT_ADDRESS: Optional[str] = None
    CONTRIBUTION_REGISTRY_ADDRESS: Optional[str] = None
    
    # IPFS Configuration
    IPFS_HOST: str = "127.0.0.1"
    IPFS_PORT: int = 5001
    IPFS_GATEWAY: str = "http://127.0.0.1:8080/ipfs/"
    
    # AI/ML Configuration
    SBERT_MODEL: str = "all-MiniLM-L6-v2"
    MIN_ABSTRACT_LENGTH: int = 100
    NOVELTY_THRESHOLD: float = 0.3
    FRAUD_DETECTION_THRESHOLD: float = 0.85
    
    # UGC Credit Points
    UGC_REFEREED_JOURNAL: int = 25
    UGC_INTERNATIONAL_BOOK: int = 30
    UGC_NATIONAL_BOOK: int = 20
    UGC_BOOK_CHAPTER: int = 5
    UGC_INTERNATIONAL_LECTURE: int = 7
    UGC_NATIONAL_CONFERENCE: int = 10
    UGC_PATENT_FILED: int = 15
    UGC_PATENT_GRANTED: int = 30
    UGC_EDITORIAL_WORK: int = 10
    UGC_RESEARCH_PROJECT: int = 20
    
    # Performance
    MAX_TPS: int = 30
    P95_LATENCY_MS: int = 300
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = [".pdf"]

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            val = v.strip().lower()
            if val in {"1", "true", "t", "yes", "on", "debug", "dev"}:
                return True
            if val in {"0", "false", "f", "no", "off", "prod", "production", "release"}:
                return False
        # fallback: truthiness
        return bool(v)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
