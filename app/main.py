import asyncio
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import asyncpg
import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="SQL Isolation Level Demo")


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


@app.post("/upload_dump")
async def upload_dump(file: UploadFile = File(...)) -> JSONResponse:
    """Загружает и восстанавливает дамп базы данных"""
    temp_dir = tempfile.mkdtemp()
    dump_path = Path(temp_dir) / file.filename

    try:
        content = await file.read()
        with open(dump_path, "wb") as f:
            f.write(content)

        if file.filename.endswith(".sql"):
            cmd = [
                "psql",
                f"-h{db_config.host}",
                f"-p{db_config.port}",
                f"-U{db_config.user}",
                f"-d{db_config.database}",
                "-f",
                str(dump_path),
            ]
            env_vars = os.environ.copy()
            env_vars["PGPASSWORD"] = db_config.password

            result = subprocess.run(cmd, env=env_vars, capture_output=True, text=True)

            if result.returncode == 0:
                return JSONResponse(
                    content={
                        "status": "success",
                        "message": f"Дамп {file.filename} успешно загружен и восстановлен",
                        "output": result.stdout,
                    }
                )
            else:
                return JSONResponse(
                    content={
                        "status": "error",
                        "message": "Ошибка восстановления дампа",
                        "error": result.stderr,
                    },
                    status_code=400,
                )
        else:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Поддерживаются только .sql файлы",
                },
                status_code=400,
            )

    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка: {str(e)}"}, status_code=500
        )
    finally:
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


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
        try:
            version = await conn.fetchval("SELECT version()")
            tables = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        finally:
            await conn.close()

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Подключено к {db_config.database}",
                "version": version,
                "tables": [{"name": t["table_name"]} for t in tables],
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка подключения: {str(e)}"},
            status_code=400,
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
    options_html = "\n".join(
        [f'<option value="{level}">{level}</option>' for level in ISOLATION_LEVELS]
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>SQL Isolation Demo</title>
    <style>
        body {{ font-family: Arial; margin: 40px; }}
        textarea {{ width: 100%; font-family: monospace; }}
        button {{ padding: 10px 20px; margin: 10px; }}
        .result {{ border: 1px solid #ccc; margin: 10px 0; padding: 10px; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    </style>
    </head>
    <body>
        <h1>SQL Isolation Level Demo</h1>
        <h3>Подключение к PostgreSQL</h3>
        <div>
            <input type="text" id="host" placeholder="Хост" value="localhost">
            <input type="text" id="port" placeholder="Порт" value="5432">
            <input type="text" id="user" placeholder="Пользователь" value="postgres">
            <input type="password" id="password" placeholder="Пароль">
            <input type="text" id="database" placeholder="БД" value="postgres">
            <button onclick="connect()">Подключиться</button>
        </div>
        <h3>Уровень изоляции</h3>
        <select id="isolation">{options_html}</select>
        <h3>Запрос 1</h3>
        <textarea id="query1" rows="5" cols="80" placeholder="SELECT * FROM ..."></textarea>
        <h3>Запрос 2</h3>
        <textarea id="query2" rows="5" cols="80" placeholder="UPDATE ..."></textarea>
        <br><button onclick="execute()">Выполнить параллельно</button>
        <div id="results"></div>
        <script>
            async function connect() {{
                const data = {{
                    host: document.getElementById('host').value,
                    port: document.getElementById('port').value,
                    user: document.getElementById('user').value,
                    password: document.getElementById('password').value,
                    database: document.getElementById('database').value
                }};
                const response = await fetch('/connect_db', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                const result = await response.json();
                alert(result.message);
            }}
            async function execute() {{
                const response = await fetch('/execute', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        query1: document.getElementById('query1').value,
                        query2: document.getElementById('query2').value,
                        isolation_level: document.getElementById('isolation').value
                    }})
                }});
                const data = await response.json();
                let html = '<h3>Результаты:</h3>';
                for (const result of data.results) {{
                    html += '<div class="result">';
                    html += '<b>Запрос ' + result.query_num + '</b><br>';
                    if (result.success) {{
                        html += '<span class="success">✓ Успешно</span><br>';
                        if (result.data && result.data.length > 0) {{
                            html += '<table>';
                            const headers = Object.keys(result.data[0]);
                            html += '<tr>';
                            for (const h of headers) html += '<th>' + h + '</th>';
                            html += '</tr>';
                            for (const row of result.data) {{
                                html += '<tr>';
                                for (const v of Object.values(row)) {{
                                    html += '<td>' + (v !== null ? v : 'NULL') + '</td>';
                                }}
                                html += '</tr>';
                            }}
                            html += '</table>';
                        }}
                    }} else {{
                        html += '<span class="error">✗ Ошибка: ' + result.error + '</span>';
                    }}
                    html += '</div>';
                }}
                document.getElementById('results').innerHTML = html;
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


if __name__ == "__main__":
    print("🚀 Запуск сервера на http://localhost:8000")
    print("📝 Убедитесь, что PostgreSQL запущен")
    uvicorn.run(app, host="127.0.0.1", port=8000)
