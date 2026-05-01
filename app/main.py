import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routers import connection_router, execute_router, pages_router
from app.config import BASE_DIR, app_config

app = FastAPI(title=app_config.title)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(connection_router)
app.include_router(execute_router)
app.include_router(pages_router)


if __name__ == "__main__":
    print("🚀 Запуск сервера на http://localhost:8000")
    uvicorn.run(app, host=app_config.host, port=app_config.port)
