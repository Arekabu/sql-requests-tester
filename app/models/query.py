from enum import StrEnum

from pydantic import BaseModel


class IsolationLevel(StrEnum):
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class SQLQuery(BaseModel):
    query1: str
    query2: str
    isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED
