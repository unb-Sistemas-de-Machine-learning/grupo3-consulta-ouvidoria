"""
ETL Processor for extracting, transforming, and loading documents.
Handles web scraping, file conversion, and integration with document ingestion.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from llama_index.core.node_parser import SentenceSplitter
import json

from src.etl.exceptions import DocumentProcessingError, ETLProcessError
from src.etl.loader import DocumentLoader, FileWrapper
from src.etl.scraper import Scraper, WikiSource

logger = logging.getLogger(__name__)

class ETLProcessor:
    """
    ETL Processor for extracting, transforming, and loading documents.
    Supports multiple extractors and transformers.
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        document_loader: Optional[DocumentLoader] = None
    ):
        """
        Initialize ETL Processor.
        
        Args:
            output_dir: Directory where processed files will be saved. 
                       Defaults to data/processed/
            document_loader: Optional DocumentLoader instance for auto-ingestion
        """
        self.output_dir = Path(output_dir) if output_dir else Path("data/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.document_loader = document_loader or DocumentLoader()
        self.extractors: Dict[str, Callable] = {}
        self.transformers: Dict[str, Callable] = {}
        
        logger.info(f"ETLProcessor initialized with output_dir: {self.output_dir}")
    
    def register_extractor(self, name: str, extractor_func: Callable):
        """
        Register an extractor function.
        
        Args:
            name: Name identifier for the extractor
            extractor_func: Function that extracts data and returns list of file paths or FileWrapper objects
        """
        self.extractors[name] = extractor_func
        logger.info(f"Registered extractor: {name}")
    
    def register_transformer(self, name: str, transformer_func: Callable):
        """
        Register a transformer function.
        
        Args:
            name: Name identifier for the transformer
            transformer_func: Function that transforms data and returns file path or FileWrapper
        """
        self.transformers[name] = transformer_func
        logger.info(f"Registered transformer: {name}")
    
    def extract(
        self,
        extractor_name: str,
        *args,
        **kwargs
    ) -> List[Any]:
        """
        Run an extractor to get raw data/files.
        
        Args:
            extractor_name: Name of registered extractor
            *args, **kwargs: Arguments to pass to extractor function
        
        Returns:
            List of extracted items (file paths, FileWrapper objects, etc.)
        
        Raises:
            ETLProcessError: If extraction fails
        """
        if extractor_name not in self.extractors:
            raise ETLProcessError(f"Extractor '{extractor_name}' not registered")
        
        try:
            logger.info(f"Running extractor: {extractor_name}")
            result = self.extractors[extractor_name](*args, **kwargs)
            logger.info(f"Extractor '{extractor_name}' completed successfully")
            return result if isinstance(result, list) else [result]
        except Exception as e:
            logger.error(f"Error in extractor '{extractor_name}': {e}")
            raise ETLProcessError(f"Extraction failed: {e}") from e
    
    def transform(
        self,
        transformer_name: str,
        input_data: Any,
        *args,
        **kwargs
    ) -> Any:
        """
        Run a transformer on extracted data.
        
        Args:
            transformer_name: Name of registered transformer
            input_data: Data to transform
            *args, **kwargs: Additional arguments for transformer
        
        Returns:
            Transformed data (file path, FileWrapper, etc.)
        
        Raises:
            ETLProcessError: If transformation fails
        """
        if transformer_name not in self.transformers:
            raise ETLProcessError(f"Transformer '{transformer_name}' not registered")
        
        try:
            logger.info(f"Running transformer: {transformer_name}")
            result = self.transformers[transformer_name](input_data, *args, **kwargs)
            logger.info(f"Transformer '{transformer_name}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in transformer '{transformer_name}': {e}")
            raise ETLProcessError(f"Transformation failed: {e}") from e
    
    def save_processed_file(
        self,
        file_wrapper: FileWrapper,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save a processed file to the output directory.
        
        Args:
            file_wrapper: FileWrapper with processed content
            filename: Optional custom filename. If None, uses file_wrapper.name
        
        Returns:
            Path to saved file
        """
        filename = filename or file_wrapper.name
        file_path = self.output_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(file_wrapper.getbuffer())
        return file_path
    
    def run_pipeline(
        self,
        extractor_name: str,
        transformer_name: Optional[str] = None,
        auto_ingest: bool = True,
        save_files: bool = True,
        extractor_args: Optional[Dict] = None,
        transformer_args: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Run a complete ETL pipeline: Extract -> Transform -> Load.
        
        Args:
            extractor_name: Name of extractor to use
            transformer_name: Optional transformer name. If None, skips transformation
            auto_ingest: If True, automatically ingest processed files into RAG system
            save_files: If True, save processed files to output directory
            extractor_args: Optional dict of arguments for extractor
            transformer_args: Optional dict of arguments for transformer
        
        Returns:
            Dict with pipeline results:
            {
                'success': bool,
                'extracted_count': int,
                'processed_files': List[str],
                'ingested': bool,
                'message': str
            }
        """
        logger.info("=" * 60)
        logger.info(f"Starting ETL pipeline: {extractor_name}")
        if transformer_name:
            logger.info(f"  Transformer: {transformer_name}")
        logger.info("=" * 60)
        
        extractor_args = extractor_args or {}
        transformer_args = transformer_args or {}
        
        try:
            # Step 1: Extract
            extracted_items = self.extract(extractor_name, **extractor_args)
            logger.info(f"Extracted {len(extracted_items)} item(s)")
            
            processed_files = []
            file_wrappers = []
            
            # Step 2: Transform (if transformer specified)
            for item in extracted_items:
                if transformer_name:
                    transformed = self.transform(transformer_name, item, **transformer_args)
                else:
                    transformed = item
                
                # Convert to FileWrapper if needed
                if isinstance(transformed, FileWrapper):
                    file_wrapper = transformed
                elif isinstance(transformed, (str, Path)):
                    # Load file from path
                    file_path = Path(transformed)
                    if not file_path.exists():
                        logger.warning(f"File not found: {file_path}")
                        continue
                    with open(file_path, "rb") as f:
                        content = f.read()
                    file_wrapper = FileWrapper(name=file_path.name, content=content)
                else:
                    logger.warning(f"Unsupported transformed type: {type(transformed)}")
                    continue
                
                # Step 3: Save files (if requested)
                if save_files:
                    saved_path = self.save_processed_file(file_wrapper)
                    processed_files.append(str(saved_path))
                
                file_wrappers.append(file_wrapper)
            
            # Step 4: Auto-ingest (if requested)
            ingested = False
            if auto_ingest and file_wrappers:
                try:
                    logger.info(f"Auto-ingesting {len(file_wrappers)} processed file(s)...")
                    # This will be called by the API to ingest into RAG
                    # For now, we just prepare the file wrappers
                    ingested = True
                    logger.info("Files prepared for ingestion")
                except Exception as e:
                    logger.error(f"Auto-ingestion failed: {e}")
                    ingested = False
            
            result = {
                'success': True,
                'extracted_count': len(extracted_items),
                'processed_files': processed_files,
                'file_wrappers': file_wrappers,  # For API to use
                'ingested': ingested,
                'message': f'Pipeline completed: {len(file_wrappers)} file(s) processed'
            }
            
            logger.info("=" * 60)
            logger.info(f"ETL pipeline completed successfully")
            logger.info(f"  Processed: {len(file_wrappers)} file(s)")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            raise ETLProcessError(f"Pipeline execution failed: {e}") from e
    
    def get_processed_files(self) -> List[Path]:
        """Get list of all processed files in output directory."""
        if not self.output_dir.exists():
            return []
        
        files = [
            f for f in self.output_dir.iterdir()
            if f.is_file() and f.suffix.lower() in {'.pdf', '.txt'}
        ]
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


# Built-in extractors and transformers

def web_scraper_extractor(items: List[Dict[str, str]]) -> List[FileWrapper]:
    """
    Extract data from Wikis and return raw JSONs like FileWrappers.
    
    Args:
        items: List of dictionaries containing wiki's data (name and url) 
    """
    scraper = Scraper()
    sources = []
    
    logger.info(f"Web scraper started for {len(items)} itens.")

    for entry in items:
        if not isinstance(entry, dict) or 'url' not in entry:
            logger.warning(f"Invalid item ignored (missing url or not a dict): {entry}")
            continue
            
        name = entry.get('name', 'Unknown_Wiki')
        url = entry.get('url')
        
        # Cria o objeto WikiSource que o Scraper espera internamente
        sources.append(WikiSource(name=name, url=url))
    
    if not sources:
        logger.warning("Nenhuma fonte válida para processar.")
        return []
    
    try:
        results_data = scraper.extract_multiple_wikis(sources)
        
        output_files = []
        for data in results_data:
            json_content = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
            
            safe_name = data['wiki_name'].replace(" ", "_").replace("/", "-")
            filename = f"{safe_name}.json"
            output_files.append(FileWrapper(name=filename, content=json_content))

        return output_files
        
    except Exception as e:
        logger.error(f"Erro fatal no scraper: {e}")
        raise ETLProcessError(f"Web scraping failed: {e}") from e

def wiki_json_transformer(
    input_data: Any, 
    chunk_size: int = 1024,
    chunk_overlap: int = 200
) -> FileWrapper:
    """
    Transforms JSON structed format to linear text using LlamaIndex.
    """
    
    data = None
    if isinstance(input_data, FileWrapper):
        data = json.loads(input_data.getbuffer().decode('utf-8'))
    elif isinstance(input_data, dict):
        data = input_data
    else:
        raise ETLProcessError(f"Invalid entry: {type(input_data)}")

    wiki_name = data.get('wiki_name', 'Wiki')
    output_lines = []

    text_splitter = SentenceSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )

    def process_node(node, context_path):
        title = node.get('title', '')
        content = node.get('content', '').strip()
        
        current_path = context_path + [title] if title else context_path
        breadcrumb_str = " > ".join(current_path)
        
        if content:
            text_chunks = text_splitter.split_text(content)
            
            for i, chunk in enumerate(text_chunks):
                header = f"## Contexto: {breadcrumb_str}"
                
                if len(text_chunks) > 1:
                    header += f" (Parte {i+1}/{len(text_chunks)})"
                
                formatted_block = f"{header}\n{chunk}\n"
                output_lines.append(formatted_block)
                output_lines.append("-" * 40) 

        # Recursão para filhos
        children = node.get('sections', []) + node.get('topics', [])
        for child in children:
            process_node(child, current_path)

    logger.info(f"Transforming Wiki '{wiki_name}' with Lhamaindex ({chunk_size} tokens)")
    
    # Executa
    if 'sections' in data:
        for section in data['sections']:
            process_node(section, [wiki_name])
    else:
        process_node(data, [wiki_name])

    final_text = "\n".join(output_lines)
    safe_name = wiki_name.replace(" ", "_")
    
    return FileWrapper(
        name=f"{safe_name}_processed.txt", 
        content=final_text.encode('utf-8')
    )



def file_converter_transformer(input_path: str, output_format: str = "pdf") -> FileWrapper:
    """
    Example file converter transformer.
    Converts files between formats.
    
    Args:
        input_path: Path to input file
        output_format: Desired output format
    
    Returns:
        FileWrapper with converted content
    """
    logger.info(f"Converting file: {input_path} to {output_format}")
    # TODO: Implement actual file conversion logic
    # For now, just read the file
    file_path = Path(input_path)
    if not file_path.exists():
        raise DocumentProcessingError(f"File not found: {input_path}")
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    output_name = file_path.stem + f".{output_format}"
    return FileWrapper(name=output_name, content=content)
