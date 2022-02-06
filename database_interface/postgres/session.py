from dataclasses import dataclass
from types import TracebackType
from typing import Optional
from typing import Type

from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from database_interface.config import db_settings


def get_aad_token():
    scope: str = "https://ossrdbms-aad.database.windows.net/.default"
    credential: DefaultAzureCredential = DefaultAzureCredential()
    access_token: AccessToken = credential.get_token(scope)
    return access_token.token


DATABASE_URL = URL.create(
    "postgresql+psycopg2",
    username=db_settings.POSTGRES_USERNAME,
    password=get_aad_token(),
    host=db_settings.POSTGRES_HOSTNAME,
    port=db_settings.POSTGRES_PORT,
    database=db_settings.POSTGRES_DB
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)


@dataclass
class PostgresSessionManager:
    def __post_init__(self) -> None:
        self.db_session = SessionLocal()

    def __enter__(self) -> SessionLocal:
        return self.db_session

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.db_session.close()

    async def __aenter__(self) -> SessionLocal:
        return self.db_session

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.db_session.close()
