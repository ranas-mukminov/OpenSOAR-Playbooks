"""
Configuration management for OpenSOAR Playbooks.
Reads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql://opensoar:<YOUR_PASSWORD>@localhost:5432/opensoar"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = "<YOUR_API_KEY>"

    # Security
    secret_key: str = "your-secret-key-change-this-in-production"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"

    # Application
    app_name: str = "OpenSOAR Playbooks"
    app_version: str = "0.1.0"


# Global settings instance
settings = Settings()
