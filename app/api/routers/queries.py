from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import db_config
from app.models import SQLQuery
from app.services import execute_parallel_queries, execute_single_transaction

execute_router = APIRouter(tags=["queries"])


@execute_router.post("/execute")
async def execute_queries(sql_query: SQLQuery) -> JSONResponse:
    if sql_query.single_transaction:
        results = await execute_single_transaction(
            sql_query.query1,
            sql_query.query2,
            sql_query.isolation_level,
            db_config.get_url(),
        )
    else:
        results = await execute_parallel_queries(
            sql_query.query1,
            sql_query.query2,
            sql_query.isolation_level,
            db_config.get_url(),
        )
    return JSONResponse(content={"results": results})
