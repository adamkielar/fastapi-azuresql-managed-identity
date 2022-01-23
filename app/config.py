import secrets

from pydantic import BaseSettings


class AppSettings(BaseSettings):
    API_V1: str = "/api/v1"
    DEBUG: bool = False
    PROJECT_NAME: str = "Azure Managed Identity Test"
    SECRET_KEY: str = secrets.token_urlsafe(32)


settings = AppSettings()
