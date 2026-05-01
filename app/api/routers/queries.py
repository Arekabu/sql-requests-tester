from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import db_config
from app.models import SQLQuery
from app.services import execute_queries_sequential

execute_router = APIRouter(tags=["queries"])


@execute_router.post("/execute")
async def execute_queries(sql_query: SQLQuery) -> JSONResponse:
    results = await execute_queries_sequential(
        sql_query.query1,
        sql_query.query2,
        sql_query.isolation_level,
        db_config.get_url(),
    )
    return JSONResponse(content={"results": results})
