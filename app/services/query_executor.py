import asyncio
from typing import Any

import asyncpg
from fastapi.responses import JSONResponse


async def execute_query_with_isolation(
    query: str, isolation_level: str, conn: asyncpg.Connection
) -> dict[str, Any]:
    """Выполняет SQL запрос в транзакции с заданным уровнем изоляции"""
    try:
        await conn.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")

        commands = [cmd.strip() for cmd in query.split(";") if cmd.strip()]

        last_select_result = None
        last_modification_result = None

        for cmd in commands:
            cmd_upper = cmd.upper()

            if cmd_upper == "BEGIN":
                await conn.execute("BEGIN")
            elif cmd_upper == "COMMIT":
                await conn.execute("COMMIT")
            elif cmd_upper == "ROLLBACK":
                await conn.execute("ROLLBACK")
            elif cmd_upper.startswith("SELECT"):
                result = await conn.fetch(cmd)
                rows = [dict(row) for row in result]
                last_select_result = {
                    "success": True,
                    "rows_count": len(rows),
                    "data": rows,
                    "error": None,
                    "query_type": "SELECT",
                }
            else:
                result = await conn.execute(cmd)
                last_modification_result = {
                    "success": True,
                    "rows_count": 0,
                    "data": [],
                    "error": None,
                    "query_type": "MODIFICATION",
                    "message": result,
                }

        if last_select_result:
            return last_select_result
        elif last_modification_result:
            return last_modification_result
        else:
            return {
                "success": True,
                "rows_count": 0,
                "data": [],
                "error": None,
                "query_type": "SUCCESS",
                "message": "Все операции выполнены",
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
        await conn.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")

        result1 = await execute_query_with_isolation(query1, isolation_level, conn)
        results.append({"query_num": 1, **result1})

        result2 = await execute_query_with_isolation(query2, isolation_level, conn)
        results.append({"query_num": 2, **result2})
    finally:
        await conn.close()
    return results


async def execute_parallel_queries(
    query1: str, query2: str, isolation_level: str, db_url: str
) -> list[dict]:
    """Два запроса параллельно в разных транзакциях"""

    async def run_in_connection(query: str, level: str) -> JSONResponse | dict:
        try:
            conn = await asyncpg.connect(db_url)
            try:
                return await execute_query_with_isolation(query, level, conn)
            finally:
                await conn.close()
        except Exception as e:
            return e

    results = await asyncio.gather(
        run_in_connection(query1, isolation_level),
        run_in_connection(query2, isolation_level),
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

    return formatted_results
