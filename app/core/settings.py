import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError


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

    # Database Configuration (Supabase)
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")  # Bắt buộc, không có mặc định
    SUPABASE_ANON_KEY: str = Field(..., env="SUPABASE_ANON_KEY")  # Bắt buộc
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")  # Bắt buộc

    # Authentication
    SECRET_KEY: str = Field(..., env="SECRET_KEY")  # Bắt buộc
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Mobile-specific Settings
    PUSH_NOTIFICATION_KEY: Optional[str] = Field(default=None, env="PUSH_NOTIFICATION_KEY")
    FCM_SERVER_KEY: Optional[str] = Field(default=None, env="FCM_SERVER_KEY")
    APNS_CERT_PATH: Optional[str] = Field(default=None, env="APNS_CERT_PATH")

    # AI Configuration for Mobile
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_MODEL: str = Field(default="grok-3", env="AI_MODEL")  # Đổi sang Grok 3 (giả định)

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )

    # Mobile Data Optimization
    COMPRESSION_ENABLED: bool = Field(default=True, env="COMPRESSION_ENABLED")
    MAX_MESSAGE_SIZE: int = Field(default=4 * 1024 * 1024, env="MAX_MESSAGE_SIZE")  # 4MB

    # Streaming Configuration
    STREAM_KEEP_ALIVE_SECONDS: int = Field(default=30, env="STREAM_KEEP_ALIVE_SECONDS")
    STREAM_TIMEOUT_SECONDS: int = Field(default=300, env="STREAM_TIMEOUT_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"  # Đảm bảo encoding
        case_sensitive = True
        extra = "ignore"  # Bỏ qua các biến môi trường không được định nghĩa


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance with error handling"""
    global _settings
    if _settings is None:
        try:
            _settings = Settings(_env_file=os.getenv("ENV_FILE", ".env"))
            print("Settings loaded successfully:", _settings.dict())
        except ValidationError as e:
            raise RuntimeError(f"Failed to load settings: {e}")
    return _settings


# Mobile-specific configurations (có thể tích hợp vào Settings sau)
class MobileConfig:
    """Mobile client optimizations"""
    BINARY_SERIALIZATION = True
    COMPRESSION_ENABLED = True
    HTTP2_CONNECTION_REUSE = True
    KEEP_ALIVE_INTERVAL = 30  # seconds
    CONNECTION_TIMEOUT = 10  # seconds
    MAX_RESPONSE_SIZE = 1024 * 1024  # 1MB
    STREAMING_CHUNK_SIZE = 64 * 1024  # 64KB
    NOTIFICATION_BATCH_SIZE = 100
    NOTIFICATION_RETRY_ATTEMPTS = 3