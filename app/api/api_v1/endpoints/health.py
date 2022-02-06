from typing import Dict
from typing import Generator

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database_interface.mssql.session import MssqlSessionManager
from database_interface.postgres.session import PostgresSessionManager

router = APIRouter()


async def get_mssql_session() -> Generator:
    with MssqlSessionManager() as mssql_db_session:
        yield mssql_db_session


async def get_postgres_session() -> Generator:
    with PostgresSessionManager() as postgres_db_session:
        yield postgres_db_session


@router.get("/mssql_db")
async def mssql_db_health(db_session: Session = Depends(get_mssql_session)) -> Dict[str, str]:
    db_version = db_session.execute(text("SELECT @@version")).scalar()
    return {"mssql version": db_version}


@router.get("/postgres_db")
async def postgres_db_health(db_session: Session = Depends(get_postgres_session)) -> Dict[str, str]:
    db_version = db_session.execute(text("SELECT version()")).scalar()
    return {"postgres version": db_version}
