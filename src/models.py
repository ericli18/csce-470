from pydantic import BaseModel


class RawQuery(BaseModel):
    query: str


class Query(BaseModel):
    raw_query: RawQuery
    query_vector: list[str]
