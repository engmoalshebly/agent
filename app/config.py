"""
SAIA Insurance Broker Platform - Configuration Management
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application Settings"""
    
    # API
    API_TITLE: str = "SAIA - كونكر لوساطة التأمين | Bineyes"
    API_VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PORT: int = 3300
    
    # Security
    API_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    
    # PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "saia_insurance"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    POSTGRESQL_URL: Optional[str] = None
    
    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017/"
    MONGO_DB_NAME: str = "saia_conversations"
    
    # LLM - Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: float = 0.3
    
    # LLM - OpenAI
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.0
    
    # Session settings
    SESSION_TIMEOUT_HOURS: int = 24
    SESSION_IDLE_TIMEOUT_MINUTES: int = 30
    
    # Invoice settings
    INVOICE_EXPIRY_HOURS: int = 24
    VAT_RATE: float = 0.15
    
    # Observability
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # WhatsApp Cloud API
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_APP_SECRET: Optional[str] = None
    WHATSAPP_API_VERSION: str = "v21.0"
    
    # PostgreSQL Pool & Timeouts
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    SQL_TIMEOUT_SECONDS: int = 30
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL"""
        if self.POSTGRESQL_URL:
            return self.POSTGRESQL_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

