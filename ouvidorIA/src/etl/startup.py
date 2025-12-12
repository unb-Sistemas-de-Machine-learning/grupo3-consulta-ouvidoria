"""
ETL Startup Module
Handles ETL pipeline execution before API initialization.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.etl.processor import ETLProcessor
from src.etl.loader import DocumentLoader
from src.etl.exceptions import ETLProcessError

logger = logging.getLogger(__name__)


def parse_etl_pipelines_config(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse ETL pipelines configuration from file or environment.
    
    Args:
        config_path: Optional path to JSON config file. 
                    If None, reads from ETL_CONFIG_PATH env var or default location.
    
    Returns:
        List of pipeline configurations
    """
    if config_path is None:
        config_path = os.getenv("ETL_CONFIG_PATH", "etl_config.json")
    
    config_file = Path(config_path)
    
    # Try to load from file
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if isinstance(config, list):
                return config
            elif isinstance(config, dict) and 'pipelines' in config:
                return config['pipelines']
            else:
                logger.warning(f"Invalid ETL config format in {config_path}. Expected list or dict with 'pipelines' key.")
                return []
        except Exception as e:
            logger.error(f"Error reading ETL config from {config_path}: {e}")
            return []
    
    # Try environment variable as JSON string
    env_config = os.getenv("ETL_PIPELINES_CONFIG")
    if env_config:
        try:
            config = json.loads(env_config)
            if isinstance(config, list):
                return config
            elif isinstance(config, dict) and 'pipelines' in config:
                return config['pipelines']
        except Exception as e:
            logger.error(f"Error parsing ETL config from environment: {e}")
    
    # Default: return empty list (no ETL pipelines configured)
    logger.info("No ETL configuration found. ETL will be skipped.")
    return []


def run_startup_etl(
    document_loader: Optional[DocumentLoader] = None,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run ETL pipelines on startup before API initialization.
    
    Args:
        document_loader: Optional DocumentLoader instance
        config_path: Optional path to ETL configuration file
    
    Returns:
        Dict with ETL execution results:
        {
            'success': bool,
            'pipelines_run': int,
            'files_processed': int,
            'errors': List[str]
        }
    """
    logger.info("=" * 60)
    logger.info("Starting ETL processes on startup...")
    logger.info("=" * 60)
    
    # Initialize document loader if not provided
    if document_loader is None:
        document_loader = DocumentLoader()
    
    # Initialize ETL processor
    etl_processor = ETLProcessor(document_loader=document_loader)
    
    # Register built-in extractors and transformers
    from src.etl.processor import web_scraper_extractor, file_converter_transformer
    etl_processor.register_extractor("web_scraper", web_scraper_extractor)
    etl_processor.register_transformer("file_converter", file_converter_transformer)
    
    # Parse ETL configuration
    pipelines_config = parse_etl_pipelines_config(config_path)
    
    results = {
        'success': True,
        'pipelines_run': 0,
        'files_processed': 0,
        'qdrant_built': False,
        'documents_indexed': 0,
        'errors': []
    }
    
    # Run ETL pipelines if configured
    if not pipelines_config:
        logger.info("No ETL pipelines configured. Skipping ETL execution.")
        return {
            'success': True,
            'pipelines_run': 0,
            'files_processed': 0,
            'errors': []
        }
    
    results = {
        'success': True,
        'pipelines_run': 0,
        'files_processed': 0,
        'errors': []
    }
    
    logger.info(f"Found {len(pipelines_config)} ETL pipeline(s) to execute")
    
    # Execute each configured pipeline
    
    for i, pipeline_config in enumerate(pipelines_config, 1):
        pipeline_name = pipeline_config.get('name', f'pipeline_{i}')
        extractor_name = pipeline_config.get('extractor')
        transformer_name = pipeline_config.get('transformer')
        auto_ingest = pipeline_config.get('auto_ingest', False)  # Don't auto-ingest during startup
        save_files = pipeline_config.get('save_files', True)
        extractor_args = pipeline_config.get('extractor_args', {})
        transformer_args = pipeline_config.get('transformer_args', {})
        
        if not extractor_name:
            error_msg = f"Pipeline '{pipeline_name}': Missing required 'extractor' field"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
            continue
        
        logger.info(f"Executing pipeline {i}/{len(pipelines_config)}: {pipeline_name}")
        logger.info(f"  Extractor: {extractor_name}")
        if transformer_name:
            logger.info(f"  Transformer: {transformer_name}")
        
        try:
            pipeline_result = etl_processor.run_pipeline(
                extractor_name=extractor_name,
                transformer_name=transformer_name,
                auto_ingest=auto_ingest,  # False during startup - will ingest later
                save_files=save_files,
                extractor_args=extractor_args,
                transformer_args=transformer_args
            )
            
            if pipeline_result['success']:
                results['pipelines_run'] += 1
                results['files_processed'] += pipeline_result.get('extracted_count', 0)
                logger.info(f"✓ Pipeline '{pipeline_name}' completed successfully")
                logger.info(f"  Processed {pipeline_result.get('extracted_count', 0)} file(s)")
            else:
                error_msg = f"Pipeline '{pipeline_name}' returned success=False"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['success'] = False
                
        except ETLProcessError as e:
            error_msg = f"Pipeline '{pipeline_name}' failed: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
        except Exception as e:
            error_msg = f"Pipeline '{pipeline_name}' unexpected error: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
    
    logger.info("=" * 60)
    if results['success']:
        logger.info(f"ETL startup completed successfully")
        logger.info(f"  Pipelines executed: {results['pipelines_run']}")
        logger.info(f"  Files processed: {results['files_processed']}")
    else:
        logger.warning(f"ETL startup completed with errors")
        logger.warning(f"  Pipelines executed: {results['pipelines_run']}")
        logger.warning(f"  Files processed: {results['files_processed']}")
        logger.warning(f"  Errors: {len(results['errors'])}")
        for error in results['errors']:
            logger.warning(f"    - {error}")
    logger.info("=" * 60)
    
    return results
