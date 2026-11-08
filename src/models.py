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
