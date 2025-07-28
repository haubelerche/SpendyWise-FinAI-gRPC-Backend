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


    # Mobile-specific Settings
    FCM_SERVICE_ACCOUNT_KEY_PATH: Optional[str] = Field(default=None, env="FCM_SERVICE_ACCOUNT_KEY_PATH")

    # AI Configuration for Mobile
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    AI_MODEL: str = Field(default="xxxx", env="AI_MODEL")  #TODO: Cập nhật

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )

    # Mobile Data Optimization
    COMPRESSION_ENABLED: bool = Field(default=True, env="COMPRESSION_ENABLED")
    MAX_MESSAGE_SIZE: int = Field(default=4 * 1024 * 1024, env="MAX_MESSAGE_SIZE")
    BINARY_SERIALIZATION: bool = Field(default=True, env="BINARY_SERIALIZATION")
    HTTP2_CONNECTION_REUSE: bool = Field(default=True, env="HTTP2_CONNECTION_REUSE")
    KEEP_ALIVE_INTERVAL: int = Field(default=30, env="KEEP_ALIVE_INTERVAL")
    CONNECTION_TIMEOUT: int = Field(default=10, env="CONNECTION_TIMEOUT")
    MAX_RESPONSE_SIZE: int = Field(default=1024 * 1024, env="MAX_RESPONSE_SIZE")
    STREAMING_CHUNK_SIZE: int = Field(default=64 * 1024, env="STREAMING_CHUNK_SIZE")
    NOTIFICATION_BATCH_SIZE: int = Field(default=100, env="NOTIFICATION_BATCH_SIZE")
    NOTIFICATION_RETRY_ATTEMPTS: int = Field(default=3, env="NOTIFICATION_RETRY_ATTEMPTS")

    # Streaming Configuration
    STREAM_KEEP_ALIVE_SECONDS: int = Field(default=30, env="STREAM_KEEP_ALIVE_SECONDS")
    STREAM_TIMEOUT_SECONDS: int = Field(default=300, env="STREAM_TIMEOUT_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Bỏ qua các biến môi trường không được định nghĩa


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
            print("Settings loaded successfully:", _settings.model_dump())
        except ValidationError as e:
            raise RuntimeError(f"Failed to load settings: {e}")
    return _settings


