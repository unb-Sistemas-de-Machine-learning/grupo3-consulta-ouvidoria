from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AnalyzeDemandRequest(BaseModel):
    user_text: str


class AnalyzeDemandResponse(BaseModel):
    tipo: str
    orgao: Optional[str] = None
    resumo: Optional[str] = None
    resumo_qualificado: Optional[str] = None
    resposta_chat: str


class QueryRequest(BaseModel):
    prompt: str


class QueryResponse(BaseModel):
    response: str


class IndexInfoResponse(BaseModel):
    exists: bool
    vectors_count: Optional[int] = None
    error: Optional[str] = None


class IngestRequest(BaseModel):
    force_rebuild: bool = False


class IngestResponse(BaseModel):
    success: bool
    message: str
    documents_processed: Optional[int] = None


class ETLPipelineRequest(BaseModel):
    extractor_name: str
    transformer_name: Optional[str] = None
    auto_ingest: bool = True
    save_files: bool = True
    extractor_args: Optional[Dict[str, Any]] = None
    transformer_args: Optional[Dict[str, Any]] = None


class ETLPipelineResponse(BaseModel):
    success: bool
    extracted_count: int
    processed_files: List[str]
    ingested: bool
    message: str
