"""
CivicSense – Application configuration.
Loads settings from .env using pydantic-settings.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="civicsense")

    # JWT
    jwt_secret: str = Field(default="change-me-to-a-random-secret-key")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=1440)

    # HuggingFace
    huggingface_api_key: str = Field(default="")

    # App
    api_base_url: str = Field(default="http://localhost:8000")
    max_image_size_mb: int = Field(default=5)

    # Initial admin bootstrap
    bootstrap_admin_name: str = "CivicSense Admin"
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton so .env is read once."""
    return Settings()
