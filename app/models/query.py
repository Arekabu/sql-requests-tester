from pydantic import BaseModel


class SQLQuery(BaseModel):
    query1: str
    query2: str
    isolation_level: str
    single_transaction: bool = False
