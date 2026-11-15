import datetime

from pydantic import BaseModel


class RawQuery(BaseModel):
    query: str


class Query(BaseModel):
    raw_query: RawQuery
    query_vector: list[str]


class MeshHeading(BaseModel):
    descriptor_id: str  # e.g. "D000787"; joins with data/mesh/mesh_descriptors.jsonl.gz
    name: str
    major_topic: bool


class Document(BaseModel):
    doc_id: str  # PMID
    title: str
    abstract: str  # "" when missing
    date: datetime.date
    mesh: list[MeshHeading]
    meta: dict


class Result(BaseModel):
    pmid: str
    title: str
    date: datetime.date
    score: float
    pub_types: list[str]
    url: str


class SearchResponse(BaseModel):
    query: str
    total: int  # matches after the date filter, before the limit
    results: list[Result]
