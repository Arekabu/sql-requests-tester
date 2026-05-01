import asyncio

import asyncpg


async def execute_query(
    query: str, isolation_level: str, conn: asyncpg.Connection
) -> dict:
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


async def execute_queries_sequential(
    query1: str, query2: str, isolation_level: str, db_url: str
) -> list[dict]:
    """Выполняет запросы последовательно в разных транзакциях"""

    async def run(query: str) -> dict:
        conn = await asyncpg.connect(db_url)
        try:
            async with conn.transaction():
                return await execute_query(query, isolation_level, conn)
        finally:
            await conn.close()

    result1, result2 = await asyncio.gather(run(query1), run(query2))

    return [
        {"query_num": 1, **result1},
        {"query_num": 2, **result2},
    ]
