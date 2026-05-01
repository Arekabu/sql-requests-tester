import asyncpg
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config import db_config

connection_router = APIRouter(tags=["connection"])


@connection_router.post("/connect_db")
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


@connection_router.get("/get_tables")
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
