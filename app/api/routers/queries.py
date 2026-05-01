import asyncio

import asyncpg
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import db_config
from app.services import execute_query_with_isolation

execute_router = APIRouter(tags=["queries"])


class SQLQuery(BaseModel):
    query1: str
    query2: str
    isolation_level: str


@execute_router.post("/execute")
async def execute_queries(sql_query: SQLQuery) -> JSONResponse:
    """Выполняет два SQL запроса параллельно"""

    async def run_in_connection(query: str, level: str) -> JSONResponse | dict:
        try:
            conn = await asyncpg.connect(db_config.get_url())
            try:
                async with conn.transaction():
                    return await execute_query_with_isolation(query, level, conn)
            finally:
                await conn.close()
        except Exception as e:
            return e

    results = await asyncio.gather(
        run_in_connection(sql_query.query1, sql_query.isolation_level),
        run_in_connection(sql_query.query2, sql_query.isolation_level),
        return_exceptions=False,
    )

    formatted_results = []
    for idx, result in enumerate(results, 1):
        if isinstance(result, Exception):
            formatted_results.append(
                {
                    "query_num": idx,
                    "success": False,
                    "error": str(result),
                    "data": [],
                    "rows_count": 0,
                    "query_type": "ERROR",
                }
            )
        else:
            formatted_results.append({"query_num": idx, **result})

    return JSONResponse(content={"results": formatted_results})
