from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
import logging

from src.api.schemas import (
    AnalyzeDemandRequest,
    AnalyzeDemandResponse,
    QueryRequest,
    QueryResponse,
    IndexInfoResponse,
    IngestRequest,
    IngestResponse,
    ETLPipelineRequest,
    ETLPipelineResponse
)
from src.rag.service import OuvidoriaRAGService
from src.etl.loader import DocumentLoader, FileWrapper
from src.etl.processor import ETLProcessor
from src.etl.startup import run_startup_etl, parse_etl_pipelines_config
from src.etl.qdrant_builder import build_qdrant_index_from_data
from src.rag.exceptions import (
    LLMConnectionError,
    QueryEngineNotReadyError,
    IndexNotReadyError,
    IndexingError
)
from src.etl.exceptions import (
    NoDocumentsFoundError,
    DocumentProcessingError,
    InvalidFileTypeError,
    ETLProcessError
)
from config import AppConfig

logger = logging.getLogger(__name__)

# Global service instances
rag_service: Optional[OuvidoriaRAGService] = None
etl_processor: Optional[ETLProcessor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    global rag_service, etl_processor
    
    # Force logging to ensure we see startup messages
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout,
        force=True
    )
    
    # Print to stdout to ensure visibility
    print("\n" + "=" * 60, flush=True)
    print("LIFESPAN STARTUP: Starting OuvidorIA API initialization...", flush=True)
    print("=" * 60 + "\n", flush=True)
    
    try:
        logger.info("=" * 60)
        logger.info("Starting OuvidorIA API initialization...")
        logger.info("=" * 60)
        
        # STEP 1: Initialize document loader (needed for ETL)
        document_loader = DocumentLoader()
        logger.info("DocumentLoader initialized")
        
        # STEP 2: Run ETL processes FIRST (before API initialization)
        logger.info("")
        logger.info(">>> STEP 1: Running ETL processes...")
        etl_results = run_startup_etl(document_loader=document_loader)
        
        if etl_results['success']:
            logger.info(f"✓ ETL completed: {etl_results['pipelines_run']} pipeline(s), {etl_results['files_processed']} file(s)")
        else:
            logger.warning(f"⚠ ETL completed with errors: {len(etl_results['errors'])} error(s)")
            # Continue anyway - API can still start
        
        # STEP 2.5: Build Qdrant index from data directory files
        logger.info("")
        logger.info(">>> STEP 1.5: Building Qdrant index from data directory...")
        # Only force rebuild if explicitly set via environment variable
        # Otherwise, let qdrant_builder decide based on whether index is empty
        import os
        force_rebuild_env = os.getenv("FORCE_REBUILD_INDEX", "false").lower() == "true"
        qdrant_result = build_qdrant_index_from_data(force_rebuild=force_rebuild_env)
        
        if qdrant_result['success']:
            if qdrant_result.get('index_created'):
                logger.info(f"✓ Qdrant index created: {qdrant_result.get('documents_indexed', 0)} document(s) indexed")
            else:
                logger.info(f"✓ Qdrant index status: {qdrant_result.get('message', 'Index already exists')}")
        else:
            logger.warning(f"⚠ Qdrant index build: {qdrant_result.get('message', 'Unknown error')}")
            # Continue anyway - will try again later
        
        # Initialize ETL processor for API endpoints
        etl_processor = ETLProcessor(document_loader=document_loader)
        logger.info("ETL Processor initialized for API endpoints")
        
        # STEP 3: Check available documents (raw + processed from ETL)
        logger.info("")
        logger.info(">>> STEP 2: Checking available documents...")
        local_doc_count = document_loader.get_local_document_count()
        processed_doc_count = document_loader.get_processed_document_count()
        total_doc_count = document_loader.get_total_document_count()
        logger.info(f"Found {local_doc_count} document(s) in raw directory")
        logger.info(f"Found {processed_doc_count} document(s) in processed directory")
        logger.info(f"Total: {total_doc_count} document(s) available")
        
        # STEP 4: Initialize RAG service
        logger.info("")
        logger.info(">>> STEP 3: Initializing RAG service...")
        rag_service = OuvidoriaRAGService(document_loader=document_loader)
        logger.info("RAG service initialized")
        
        # STEP 5: Connect LLM
        logger.info("")
        logger.info(">>> STEP 4: Connecting to LLM...")
        try:
            rag_service.connect_ollama()
            logger.info("✓ LLM connected successfully")
        except LLMConnectionError as e:
            logger.warning(f"⚠ Could not connect to Ollama on startup: {e}")
            logger.warning("LLM will be connected on first request that requires it.")
        
        # STEP 6: Verify index is ready (should already be built by ETL startup)
        logger.info("")
        logger.info(">>> STEP 5: Verifying Qdrant index...")
        index_loaded = rag_service.load_existing_index()
        
        if index_loaded:
            logger.info("✓ Qdrant index is ready")
            index_info = rag_service.get_index_info()
            vectors_count = index_info.get('vectors_count', 0)
            logger.info(f"  Index contains {vectors_count} vectors")
            logger.info(f"  Index location: {AppConfig.QDRANT_LOCATION}")
        else:
            # Index should have been built by ETL startup, but if not, try to create it
            if total_doc_count > 0:
                logger.warning("Qdrant index not found despite documents being available.")
                logger.info("Attempting to create index now...")
                try:
                    result = rag_service.ingest_and_index(
                        uploaded_files=None,
                        force_rebuild=False
                    )
                    
                    if result['success']:
                        logger.info("✓ Index created successfully")
                        logger.info(f"  Processed {result.get('documents_count', 0)} document(s)")
                    else:
                        logger.warning(f"⚠ Index creation returned success=False: {result.get('message', 'Unknown error')}")
                except NoDocumentsFoundError as e:
                    logger.warning(f"⚠ No documents found to process: {e}")
                except LLMConnectionError as e:
                    logger.warning(f"⚠ Could not create index - LLM not available: {e}")
                    logger.warning("Index will be created when LLM becomes available")
                except IndexingError as e:
                    logger.error(f"✗ Failed to create index: {e}")
                    logger.error("Index creation will be retried on next ingest request")
                except Exception as e:
                    logger.error(f"✗ Unexpected error during index creation: {e}")
                    logger.error("Index creation will be retried on next ingest request")
            else:
                logger.info("No documents available. Index will be created when documents are added.")
        
        logger.info("=" * 60)
        logger.info("API initialization complete")
        logger.info("=" * 60)
        print("\n" + "=" * 60, flush=True)
        print("LIFESPAN STARTUP: API initialization complete", flush=True)
        print("=" * 60 + "\n", flush=True)
        
    except Exception as e:
        error_msg = f"Failed to initialize RAG service: {e}"
        logger.error(error_msg)
        print(f"\nERROR: {error_msg}\n", flush=True)
        import traceback
        logger.error(traceback.format_exc())
        print(traceback.format_exc(), flush=True)
        # Don't raise - allow API to start but endpoints will return 503
        logger.error("API will start but RAG endpoints will be unavailable until service is initialized.")
        print("API will start but RAG endpoints will be unavailable until service is initialized.", flush=True)
    
    yield  # App is running
    
    # Shutdown (if needed)
    logger.info("Shutting down API...")
    print("LIFESPAN SHUTDOWN: Shutting down API...", flush=True)


app = FastAPI(
    title="OuvidorIA API",
    description="API backend for OuvidorIA RAG service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware to allow Streamlit frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if rag_service is None:
        return {
            "status": "unhealthy",
            "rag_service_ready": False,
            "message": "RAG service not initialized"
        }
    
    return {
        "status": "healthy",
        "rag_service_ready": rag_service.is_ready(),
        "llm_ready": rag_service.llm_ready,
        "query_engine_ready": rag_service.query_engine is not None,
        "index_exists": rag_service.get_index_info().get("exists", False)
    }


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_documents(
    force_rebuild: bool = False,
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Ingest and index documents.
    If files are provided, they will be processed.
    Otherwise, documents from data/raw/ will be used.
    """
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        uploaded_files = None
        if files:
            # Convert FastAPI UploadFile to FileWrapper
            file_wrappers = []
            for f in files:
                content = await f.read()
                wrapper = FileWrapper(name=f.filename, content=content)
                file_wrappers.append(wrapper)
            
            uploaded_files = file_wrappers
        
        # Ingest and index documents
        result = rag_service.ingest_and_index(
            uploaded_files=uploaded_files,
            force_rebuild=force_rebuild
        )
        
        return IngestResponse(
            success=result['success'],
            message=result.get('message', 'Documents processed'),
            documents_processed=result.get('documents_count', 0)
        )
    
    except (NoDocumentsFoundError, InvalidFileTypeError) as e:
        logger.error(f"Document error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DocumentProcessingError as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process documents: {e}")
    except LLMConnectionError as e:
        logger.error(f"LLM connection error: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except IndexingError as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error ingesting documents: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get("/api/index/info", response_model=IndexInfoResponse)
async def get_index_info():
    """Get information about the current index."""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        info = rag_service.get_index_info()
        return IndexInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting index info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the RAG system with a prompt.
    Returns a response based on the indexed documents.
    """
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        response = rag_service.query(request.prompt)
        return QueryResponse(response=str(response))
    except QueryEngineNotReadyError as e:
        logger.error(f"Query engine not ready: {e}")
        raise HTTPException(
            status_code=400,
            detail="Query engine not initialized. Please ingest documents first."
        )
    except LLMConnectionError as e:
        logger.error(f"LLM connection error: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        logger.error(f"Error querying: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.post("/api/analyze", response_model=AnalyzeDemandResponse)
async def analyze_demand(request: AnalyzeDemandRequest):
    """
    Analyze a user demand and return structured information.
    This is the main endpoint used by the frontend for form assistance.
    """
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        # analyze_demand now returns a dict directly, no JSON parsing needed
        result = rag_service.analyze_demand(request.user_text)
        
        return AnalyzeDemandResponse(**result)
    except QueryEngineNotReadyError as e:
        logger.error(f"Query engine not ready: {e}")
        raise HTTPException(
            status_code=400,
            detail="Query engine not initialized. Please ingest documents first."
        )
    except LLMConnectionError as e:
        logger.error(f"LLM connection error: {e}")
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
    except Exception as e:
        logger.error(f"Error analyzing demand: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@app.post("/api/etl/run", response_model=ETLPipelineResponse)
async def run_etl_pipeline(request: ETLPipelineRequest):
    """
    Run an ETL pipeline to extract, transform, and optionally ingest documents.
    """
    if etl_processor is None:
        raise HTTPException(status_code=503, detail="ETL processor not initialized")
    
    try:
        # Run ETL pipeline
        result = etl_processor.run_pipeline(
            extractor_name=request.extractor_name,
            transformer_name=request.transformer_name,
            auto_ingest=request.auto_ingest,
            save_files=request.save_files,
            extractor_args=request.extractor_args or {},
            transformer_args=request.transformer_args or {}
        )
        
        # If auto_ingest is enabled and we have file wrappers, ingest them
        if request.auto_ingest and rag_service and result.get('file_wrappers'):
            try:
                logger.info(f"Auto-ingesting {len(result['file_wrappers'])} file(s) from ETL...")
                ingest_result = rag_service.ingest_and_index(
                    uploaded_files=result['file_wrappers'],
                    force_rebuild=False
                )
                result['ingested'] = ingest_result['success']
                if ingest_result['success']:
                    result['message'] += f" | Ingested {ingest_result.get('documents_count', 0)} document(s)"
            except Exception as e:
                logger.error(f"Auto-ingestion failed: {e}")
                result['ingested'] = False
                result['message'] += f" | Ingestion failed: {e}"
        
        return ETLPipelineResponse(**result)
    
    except ETLProcessError as e:
        logger.error(f"ETL process error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error running ETL pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"ETL pipeline failed: {e}")


@app.get("/api/etl/status")
async def get_etl_status():
    """Get status of ETL processor and processed files."""
    if etl_processor is None:
        raise HTTPException(status_code=503, detail="ETL processor not initialized")
    
    try:
        processed_files = etl_processor.get_processed_files()
        return {
            "status": "ready",
            "registered_extractors": list(etl_processor.extractors.keys()),
            "registered_transformers": list(etl_processor.transformers.keys()),
            "processed_files_count": len(processed_files),
            "processed_files": [str(f) for f in processed_files[:10]],  # Last 10 files
            "output_directory": str(etl_processor.output_dir)
        }
    except Exception as e:
        logger.error(f"Error getting ETL status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
