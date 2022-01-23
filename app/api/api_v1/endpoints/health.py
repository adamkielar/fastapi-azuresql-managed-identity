from typing import Dict
from typing import Generator

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database_interface.mssql.session import DBSessionManager

router = APIRouter()


async def get_db_session() -> Generator:
    with DBSessionManager() as db_session:
        yield db_session


@router.get("/mssql_db")
async def mssql_db_health(db_session: Session = Depends(get_db_session, use_cache=False)) -> Dict[str, str]:
    db_version = db_session.execute(text("SELECT @@version")).scalar()
    return {"mssql version": db_version}
