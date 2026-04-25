import asyncio
import os
from pathlib import Path
from typing import Any

import asyncpg
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
app = FastAPI(title="SQL Isolation Level Demo")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "password")
        self.database = os.getenv("DB_NAME", "isolation_demo")

    def get_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


db_config = DatabaseConfig()


class SQLQuery(BaseModel):
    query1: str
    query2: str
    isolation_level: str


ISOLATION_LEVELS = [
    "READ UNCOMMITTED",
    "READ COMMITTED",
    "REPEATABLE READ",
    "SERIALIZABLE",
]


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


@app.post("/execute")
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


@app.post("/connect_db")
async def connect_db(db_params: dict) -> JSONResponse:
    """Подключается к указанной базе данных"""
    try:
        db_config.host = db_params.get("host", "db")
        db_config.port = db_params.get("port", "5432")
        db_config.user = db_params.get("user", "postgres")
        db_config.password = db_params.get("password", "postgres123")
        db_config.database = db_params.get("database", "isolation_demo")

        conn = await asyncpg.connect(db_config.get_url())
        await conn.close()

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Подключено к {db_config.database}",
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка подключения: {str(e)}"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.get("/get_tables")
async def get_tables() -> JSONResponse:
    """Получает список всех таблиц в текущей БД"""
    try:
        conn = await asyncpg.connect(db_config.get_url())
        try:
            tables = await conn.fetch("""
                SELECT
                    table_name,
                    (SELECT count(*) FROM information_schema.columns
                     WHERE table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        finally:
            await conn.close()

        return JSONResponse(
            content={
                "status": "success",
                "tables": [
                    {"name": t["table_name"], "columns": t["column_count"]}
                    for t in tables
                ],
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=400
        )


# пока с шаблонами не разобрался
@app.get("/", response_class=HTMLResponse)
async def get_demo_page(request: Request) -> HTMLResponse:

    html_path = Path(BASE_DIR / "templates/index.html")
    html_content = html_path.read_text(encoding="utf-8")

    options_html = "\n".join(
        [f'<option value="{level}">{level}</option>' for level in ISOLATION_LEVELS]
    )

    html_content = html_content.replace("{options_html}", options_html)
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    print("🚀 Запуск сервера на http://localhost:8000")
    print("📝 Убедитесь, что PostgreSQL запущен")
    uvicorn.run(app, host="127.0.0.1", port=8000)
