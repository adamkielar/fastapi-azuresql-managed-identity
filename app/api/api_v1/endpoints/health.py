from typing import Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/mssql_db")
async def mssql_db_health() -> Dict[str, str]:
    return {"ping": "pong"}
