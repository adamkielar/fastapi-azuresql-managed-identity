import os

from pydantic import BaseSettings


class DbSettings(BaseSettings):
    DB_CONNECTION_STRING: str = os.environ.get("CONNECTION_STRING")


db_settings = DbSettings()
