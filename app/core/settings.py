# Application settings and configuration

"""
gRPC Server Settings - Optimized for Mobile Clients
Binary protocol with compression and connection reuse
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with gRPC-first configuration"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # gRPC Server Configuration
    GRPC_HOST: str = Field(default="0.0.0.0", env="GRPC_HOST")
    GRPC_PORT: int = Field(default=50051, env="GRPC_PORT")
    GRPC_MAX_WORKERS: int = Field(default=10, env="GRPC_MAX_WORKERS")
    
    # TLS Configuration for Production
    TLS_ENABLED: bool = Field(default=False, env="TLS_ENABLED")
    TLS_CERT_PATH: Optional[str] = Field(default=None, env="TLS_CERT_PATH")
    TLS_KEY_PATH: Optional[str] = Field(default=None, env="TLS_KEY_PATH")
    
    # Database Configuration
    DATABASE_URL: str = Field(env="DATABASE_URL")
    SUPABASE_URL: str = Field(env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(env="SUPABASE_KEY")
    
    # Authentication
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Mobile-specific Settings
    PUSH_NOTIFICATION_KEY: Optional[str] = Field(default=None, env="PUSH_NOTIFICATION_KEY")
    FCM_SERVER_KEY: Optional[str] = Field(default=None, env="FCM_SERVER_KEY")
    APNS_CERT_PATH: Optional[str] = Field(default=None, env="APNS_CERT_PATH")
    
    # AI/ML Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_MODEL: str = Field(default="gpt-3.5-turbo", env="AI_MODEL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Connection Pool Settings (removing Redis/Celery)
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=30, env="DB_MAX_OVERFLOW")
    
    # Rate Limiting (gRPC interceptors)
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    # Mobile Data Optimization
    COMPRESSION_ENABLED: bool = Field(default=True, env="COMPRESSION_ENABLED")
    MAX_MESSAGE_SIZE: int = Field(default=4 * 1024 * 1024, env="MAX_MESSAGE_SIZE")  # 4MB
    
    # Streaming Configuration
    STREAM_KEEP_ALIVE_SECONDS: int = Field(default=30, env="STREAM_KEEP_ALIVE_SECONDS")
    STREAM_TIMEOUT_SECONDS: int = Field(default=300, env="STREAM_TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Mobile-specific configurations
class MobileConfig:
    """Mobile client optimizations"""
    
    # Binary protocol advantages
    BINARY_SERIALIZATION = True
    COMPRESSION_ENABLED = True
    HTTP2_CONNECTION_REUSE = True
    
    # Battery optimization
    KEEP_ALIVE_INTERVAL = 30  # seconds
    CONNECTION_TIMEOUT = 10   # seconds
    
    # Data usage optimization
    MAX_RESPONSE_SIZE = 1024 * 1024  # 1MB
    STREAMING_CHUNK_SIZE = 64 * 1024  # 64KB
    
    # Push notification settings
    NOTIFICATION_BATCH_SIZE = 100
    NOTIFICATION_RETRY_ATTEMPTS = 3
