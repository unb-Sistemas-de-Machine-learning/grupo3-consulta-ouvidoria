"""
Qdrant Index Builder
Creates Qdrant vector index from data directory files before API initialization.
"""
import os
import logging
from typing import Dict, Any, Optional

from src.etl.loader import DocumentLoader
from src.rag.exceptions import LLMConnectionError, IndexingError
from config import AppConfig

logger = logging.getLogger(__name__)


def build_qdrant_index_from_data(
    data_dir: Optional[str] = None,
    force_rebuild: bool = False
) -> Dict[str, Any]:
    """
    Build Qdrant vector index from files in data directory before API initialization.
    
    Args:
        data_dir: Optional path to data directory. Defaults to data/raw
        force_rebuild: If True, rebuilds index even if it exists
    
    Returns:
        Dict with build results:
        {
            'success': bool,
            'index_created': bool,
            'documents_indexed': int,
            'message': str
        }
    """
    logger.info("=" * 60)
    logger.info("Building Qdrant index from data directory...")
    logger.info("=" * 60)
    
    try:
        # Initialize document loader
        if data_dir:
            document_loader = DocumentLoader(local_data_dir=data_dir)
        else:
            document_loader = DocumentLoader()
        
        # Check if documents exist
        total_doc_count = document_loader.get_total_document_count()
        local_doc_count = document_loader.get_local_document_count()
        processed_doc_count = document_loader.get_processed_document_count()
        
        logger.info(f"Found {local_doc_count} document(s) in raw directory")
        logger.info(f"Found {processed_doc_count} document(s) in processed directory")
        logger.info(f"Total: {total_doc_count} document(s) available")
        
        if total_doc_count == 0:
            logger.warning("No documents found in data directory. Skipping index creation.")
            return {
                'success': True,
                'index_created': False,
                'documents_indexed': 0,
                'message': 'No documents found to index'
            }
        
        # Initialize RAG service (this initializes Qdrant connection)
        # Import here to avoid circular import
        from src.rag.service import OuvidoriaRAGService
        
        logger.info("Initializing RAG service for index creation...")
        rag_service = OuvidoriaRAGService(document_loader=document_loader)
        
        # Check if index already exists and has vectors
        index_info = rag_service.get_index_info()
        index_exists = index_info.get('exists', False)
        vectors_count = index_info.get('vectors_count', 0) if index_exists else 0
        
        logger.info(f"Index status: exists={index_exists}, vectors_count={vectors_count}, force_rebuild={force_rebuild}")
        
        # If index exists and has vectors, skip rebuilding unless explicitly forced
        if index_exists and vectors_count > 0:
            if force_rebuild:
                logger.info(f"Force rebuild requested. Existing index has {vectors_count} vectors will be deleted and rebuilt.")
            else:
                logger.info(f"Qdrant index already exists with {vectors_count} vectors. Skipping creation.")
                return {
                    'success': True,
                    'index_created': False,
                    'documents_indexed': vectors_count,
                    'message': f'Index already exists with {vectors_count} vectors'
                }
        
        # If index exists but is empty (0 vectors), we should rebuild it
        if index_exists and vectors_count == 0:
            logger.warning("Qdrant index exists but is empty (0 vectors). Rebuilding index...")
            force_rebuild = True
        
        if force_rebuild and index_exists:
            logger.info("Force rebuild enabled. Rebuilding index...")
        
        # Connect to LLM (required for indexing)
        logger.info("Connecting to LLM for indexing...")
        try:
            rag_service.connect_ollama()
            logger.info("LLM connected successfully")
        except LLMConnectionError as e:
            logger.warning(f"Could not connect to LLM: {e}")
            logger.warning("Index creation will be deferred until LLM is available.")
            return {
                'success': False,
                'index_created': False,
                'documents_indexed': 0,
                'message': f'LLM not available: {e}'
            }
        
        # Create index from documents
        logger.info(f"Creating Qdrant index from {total_doc_count} document(s)...")
        logger.info("This may take a few minutes depending on document size...")
        
        result = rag_service.ingest_and_index(
            uploaded_files=None,
            force_rebuild=force_rebuild
        )
        
        if result['success']:
            documents_count = result.get('documents_count', 0)
            logger.info("=" * 60)
            logger.info("✓ Qdrant index created successfully!")
            logger.info(f"  Documents indexed: {documents_count}")
            logger.info(f"  Index location: {AppConfig.QDRANT_LOCATION}")
            logger.info("=" * 60)
            
            return {
                'success': True,
                'index_created': True,
                'documents_indexed': documents_count,
                'message': f'Index created successfully with {documents_count} document(s)'
            }
        else:
            error_msg = result.get('message', 'Unknown error')
            logger.error(f"Index creation failed: {error_msg}")
            return {
                'success': False,
                'index_created': False,
                'documents_indexed': 0,
                'message': error_msg
            }
            
    except IndexingError as e:
        logger.error(f"Indexing error: {e}")
        return {
            'success': False,
            'index_created': False,
            'documents_indexed': 0,
            'message': f'Indexing failed: {e}'
        }
    except Exception as e:
        logger.error(f"Unexpected error building Qdrant index: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'index_created': False,
            'documents_indexed': 0,
            'message': f'Unexpected error: {e}'
        }
