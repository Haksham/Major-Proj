"""
SALF Backend Configuration
Secure Academic Ledger Framework - Core Settings
"""
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache
from urllib.parse import urlparse


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

    # Security — .env may use JWT_SECRET instead of SECRET_KEY
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"),
    )
    ALGORITHM: str = Field(
        default="HS256",
        validation_alias=AliasChoices("ALGORITHM", "JWT_ALGORITHM"),
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql://salf_user:salf_password@localhost:5432/salf_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Blockchain - Hyperledger Besu
    # docker-compose may send BESU_RPC_URL or BLOCKCHAIN_RPC_URL
    BESU_RPC_URL: str = Field(
        default="http://127.0.0.1:8545",
        validation_alias=AliasChoices("BESU_RPC_URL", "BLOCKCHAIN_RPC_URL"),
    )
    BESU_CHAIN_ID: int = 1337
    BESU_PRIVATE_KEY: Optional[str] = None

    # Contract Addresses (populated after deployment)
    ACCESS_CONTROL_ADDRESS: Optional[str] = None
    ACADEMIC_CREDIT_ADDRESS: Optional[str] = None
    CONTRIBUTION_REGISTRY_ADDRESS: Optional[str] = None

    # IPFS Configuration — .env uses IPFS_API_URL; legacy fields derived below
    IPFS_API_URL: str = Field(
        default="http://127.0.0.1:5001",
        validation_alias=AliasChoices("IPFS_API_URL", "IPFS_HOST"),
    )
    IPFS_GATEWAY_URL: str = Field(
        default="http://127.0.0.1:8080",
        validation_alias=AliasChoices("IPFS_GATEWAY_URL", "IPFS_GATEWAY"),
    )

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

    # Derived IPFS properties (parsed from IPFS_API_URL)
    @property
    def IPFS_HOST(self) -> str:
        return urlparse(self.IPFS_API_URL).hostname or "127.0.0.1"

    @property
    def IPFS_PORT(self) -> int:
        return urlparse(self.IPFS_API_URL).port or 5001

    @property
    def IPFS_GATEWAY(self) -> str:
        base = self.IPFS_GATEWAY_URL.rstrip("/")
        return f"{base}/ipfs/"

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
        return bool(v)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
