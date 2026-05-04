import asyncio

import asyncpg


async def execute_query(
    query: str, isolation_level: str, conn: asyncpg.Connection
) -> dict:
    """Выполняет SQL запрос с заданным уровнем изоляции"""

    try:
        await conn.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")

        commands = [cmd.strip() for cmd in query.split(";") if cmd.strip()]

        select_results = []
        last_modification = None

        for idx, cmd in enumerate(commands):
            cmd_upper = cmd.upper()
            is_select = cmd_upper.startswith("SELECT") or cmd_upper.startswith("WITH")

            if is_select:
                result = await conn.fetch(cmd)
                rows = [dict(row) for row in result]
                select_results.append(
                    {
                        "success": True,
                        "rows_count": len(rows),
                        "data": rows,
                        "error": None,
                        "query_type": "SELECT",
                        "select_number": len(select_results) + 1,
                    }
                )
            else:
                await conn.execute(cmd)
                last_modification = {
                    "success": True,
                    "rows_count": 0,
                    "data": [],
                    "error": None,
                    "query_type": "MODIFICATION",
                    "message": f"Выполнено: {cmd[:50]}...",
                }

        if select_results:
            if len(select_results) == 1:
                return select_results[0]

            return {
                "success": True,
                "is_multi_select": True,
                "selects": select_results,
                "query_type": "MULTI_SELECT",
                "selects_count": len(select_results),
            }

        return last_modification or {
            "success": True,
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


async def execute_queries_parallel(
    query1: str, query2: str, isolation_level: str, db_url: str
) -> list[dict]:
    """Выполняет запросы параллельно в разных транзакциях"""

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
