from typing import Any

import asyncpg


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
