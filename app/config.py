import os
from pathlib import Path

BASE_DIR = Path(__file__).parent


class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "password")
        self.database = os.getenv("DB_NAME", "isolation_demo")

    def get_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class AppConfig:
    title: str = "SQL Isolation Level Demo"
    host: str = "127.0.0.1"
    port: int = 8000


db_config = DatabaseConfig()
app_config = AppConfig()
