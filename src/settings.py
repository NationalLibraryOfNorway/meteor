"""Settings for FastAPI service"""


from functools import lru_cache

from pydantic import Extra
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Loads settings from .env file"""
    UPLOAD_FOLDER: str = 'static'

    # Should be defined in a .env file
    MOUNT_FOLDER: str = ""
    MAX_FILE_SIZE_MB: int = 0
    ENVIRONMENT: str = "local"
    LANGUAGES: str = ""
    REGISTRY_FILE: str = ""
    REGISTRY_HOST: str = ""
    REGISTRY_USER: str = ""
    REGISTRY_DATABASE: str = ""
    REGISTRY_PASSWORD: str = ""
    USE_GIELLADETECT: bool = False
    GIELLADETECT_LANGS: str = ""
    CUSTOM_PATH: str = ""

    class Config:
        """Specify name of settings file"""
        env_file = '.env'
        extra = Extra.allow


settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    return settings
