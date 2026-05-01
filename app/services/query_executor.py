import asyncio
from typing import Any

import asyncpg
from fastapi.responses import JSONResponse

from app.config import db_config
from app.models import SQLQuery


async def execute_query_with_isolation(
    query: str, isolation_level: str, conn: asyncpg.Connection
) -> dict[str, Any]:
    """Выполняет SQL запрос в транзакции с заданным уровнем изоляции"""
    try:
        await conn.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")

        query_upper = query.strip().upper()
        is_select = query_upper.startswith("SELECT") or query_upper.startswith("WITH")

        if is_select:
            result = await conn.fetch(query)
            rows = [dict(row) for row in result]
            return {
                "success": True,
                "rows_count": len(rows),
                "data": rows,
                "error": None,
                "query_type": "SELECT",
            }
        else:
            result = await conn.execute(query)
            return {
                "success": True,
                "rows_count": 0,
                "data": [],
                "error": None,
                "query_type": "MODIFICATION",
                "message": result,
            }
    except Exception as e:
        return {
            "success": False,
            "rows_count": 0,
            "data": [],
            "error": str(e),
            "query_type": "ERROR",
        }


async def execute_single_transaction(
    query1: str, query2: str, isolation_level: str, db_url: str
) -> list[dict]:
    """Оба запроса в одной транзакции"""
    results = []
    conn = await asyncpg.connect(db_url)
    try:
        async with conn.transaction():
            await conn.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")

            # Запрос 1
            result1 = await execute_query_with_isolation(query1, isolation_level, conn)
            results.append({"query_num": 1, **result1})

            # Запрос 2
            result2 = await execute_query_with_isolation(query2, isolation_level, conn)
            results.append({"query_num": 2, **result2})
    finally:
        await conn.close()
    return results


async def execute_parallel_queries(sql_query: SQLQuery) -> JSONResponse:
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
