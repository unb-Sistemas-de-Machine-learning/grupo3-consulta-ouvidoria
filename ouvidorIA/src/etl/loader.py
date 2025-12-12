import os
import shutil
import tempfile
from typing import List, Any, Optional, Union
from pathlib import Path
from llama_index.core import Document, SimpleDirectoryReader
import logging

from src.etl.exceptions import (
    NoDocumentsFoundError,
    DocumentProcessingError,
    InvalidFileTypeError
)

logger = logging.getLogger(__name__)


class FileWrapper:
    """
    Wrapper for uploaded files to provide a consistent interface.
    Works with both Streamlit UploadedFile and FastAPI UploadFile.
    """
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content
    
    def getbuffer(self) -> bytes:
        """Return file content as bytes."""
        return self._content
    
    @property
    def size(self) -> int:
        """Return file size in bytes."""
        return len(self._content)


class DocumentLoader:
    """
    Document loader for ingesting PDF and text files.
    Supports multiple sources: uploaded files, local directory, or file paths.
    Can also load from processed ETL directory.
    """
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt'}
    LOCAL_DATA_DIR = os.path.join("data", "raw")
    PROCESSED_DATA_DIR = os.path.join("data", "processed")
    
    def __init__(
        self, 
        local_data_dir: Optional[str] = None,
        include_processed: bool = True
    ):
        """
        Initialize DocumentLoader.
        
        Args:
            local_data_dir: Optional custom path for local documents directory
            include_processed: If True, also checks processed directory for ETL output
        """
        self.local_data_dir = Path(local_data_dir) if local_data_dir else Path(self.LOCAL_DATA_DIR)
        self.processed_data_dir = Path(self.PROCESSED_DATA_DIR)
        self.include_processed = include_processed
        logger.info(f"DocumentLoader initialized with local_data_dir: {self.local_data_dir}")
        if include_processed:
            logger.info(f"  Also checking processed directory: {self.processed_data_dir}")
    
    def load_documents(
        self, 
        uploaded_files: Optional[List[Union[FileWrapper, Any]]] = None
    ) -> List[Document]:
        """
        Load documents from available sources.
        Priority: uploaded_files > local_data_dir
        
        Args:
            uploaded_files: List of file wrappers or file-like objects with .name and .getbuffer()
        
        Returns:
            List of Document objects from LlamaIndex
        
        Raises:
            NoDocumentsFoundError: If no documents are found in any source
            DocumentProcessingError: If there's an error processing documents
        """
        logger.info("=" * 50)
        logger.info("DocumentLoader.load_documents() called")
        logger.info("=" * 50)
        
        # Strategy 1: Process uploaded files
        if uploaded_files:
            logger.info(f"Strategy: Processing {len(uploaded_files)} uploaded file(s)")
            return self._process_uploaded_files(uploaded_files)
        
        # Strategy 2: Load from local directory (raw + processed combined)
        # Combine files from both directories if both exist
        raw_files = []
        processed_files = []
        
        if self._local_data_exists():
            raw_files = [
                f for f in self.local_data_dir.iterdir()
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
            ]
        
        if self.include_processed and self._processed_data_exists():
            processed_files = [
                f for f in self.processed_data_dir.iterdir()
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
            ]
        
        if raw_files or processed_files:
            # Load from both directories
            all_documents = []
            
            if raw_files:
                logger.info(f"Loading {len(raw_files)} file(s) from raw directory '{self.local_data_dir}'")
                raw_docs = self._load_from_directory(self.local_data_dir)
                all_documents.extend(raw_docs)
            
            if processed_files:
                logger.info(f"Loading {len(processed_files)} file(s) from processed directory '{self.processed_data_dir}'")
                processed_docs = self._load_from_directory(self.processed_data_dir)
                all_documents.extend(processed_docs)
            
            logger.info(f"Total loaded: {len(all_documents)} document chunks from both directories")
            return all_documents
        
        # Strategy 4: No documents found
        error_msg = (
            f"No documents found! Please upload files via API, "
            f"add files (.pdf, .txt) to '{self.local_data_dir}', "
            f"or run ETL processes to generate files in '{self.processed_data_dir}'"
        )
        logger.error(error_msg)
        raise NoDocumentsFoundError(error_msg)
    
    def _local_data_exists(self) -> bool:
        """Check if local data directory exists and contains files."""
        if not self.local_data_dir.exists():
            return False
        
        # Check for supported file types
        files = [
            f for f in self.local_data_dir.iterdir() 
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]
        return len(files) > 0
    
    def _processed_data_exists(self) -> bool:
        """Check if processed data directory exists and contains files."""
        if not self.processed_data_dir.exists():
            return False
        
        # Check for supported file types
        files = [
            f for f in self.processed_data_dir.iterdir() 
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]
        return len(files) > 0
    
    def _process_uploaded_files(
        self, 
        uploaded_files: List[Union[FileWrapper, Any]]
    ) -> List[Document]:
        """
        Process uploaded files by saving them temporarily and loading with LlamaIndex.
        
        Args:
            uploaded_files: List of file objects with .name and .getbuffer() methods
        
        Returns:
            List of Document objects
        
        Raises:
            DocumentProcessingError: If processing fails
            InvalidFileTypeError: If unsupported file types are provided
        """
        # Validate file types
        for file_obj in uploaded_files:
            filename = getattr(file_obj, 'name', 'unknown')
            ext = Path(filename).suffix.lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                raise InvalidFileTypeError(
                    f"Unsupported file type: {ext}. Supported types: {self.SUPPORTED_EXTENSIONS}"
                )
        
        # Create temporary directory for processing
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="ouvidoria_docs_")
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Save uploaded files to temp directory
            for file_obj in uploaded_files:
                filename = getattr(file_obj, 'name', 'unknown')
                file_path = Path(temp_dir) / filename
                
                # Get file content
                if hasattr(file_obj, 'getbuffer'):
                    content = file_obj.getbuffer()
                elif hasattr(file_obj, 'read'):
                    content = file_obj.read()
                else:
                    raise DocumentProcessingError(
                        f"File object {filename} doesn't have getbuffer() or read() method"
                    )
                
                # Write to temp file
                with open(file_path, "wb") as f:
                    if isinstance(content, bytes):
                        f.write(content)
                    else:
                        f.write(content)
                
                logger.info(f"Saved uploaded file: {filename} ({len(content)} bytes)")
            
            # Load documents using LlamaIndex
            documents = SimpleDirectoryReader(temp_dir).load_data()
            logger.info(f"Loaded {len(documents)} document chunks from uploaded files")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error processing uploaded files: {e}")
            raise DocumentProcessingError(f"Failed to process uploaded files: {e}") from e
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
    
    def _load_from_directory(self, directory: Path) -> List[Document]:
        """
        Load documents from a local directory.
        
        Args:
            directory: Path to directory containing documents
        
        Returns:
            List of Document objects
        
        Raises:
            DocumentProcessingError: If loading fails
        """
        try:
            documents = SimpleDirectoryReader(str(directory)).load_data()
            logger.info(f"Loaded {len(documents)} document chunks from {directory}")
            return documents
        except Exception as e:
            logger.error(f"Error loading documents from directory {directory}: {e}")
            raise DocumentProcessingError(f"Failed to load documents from {directory}: {e}") from e
    
    def get_local_document_count(self) -> int:
        """Get count of documents in local directory (raw only)."""
        if not self._local_data_exists():
            return 0
        files = [
            f for f in self.local_data_dir.iterdir() 
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]
        return len(files)
    
    def get_processed_document_count(self) -> int:
        """Get count of documents in processed directory."""
        if not self._processed_data_exists():
            return 0
        files = [
            f for f in self.processed_data_dir.iterdir() 
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]
        return len(files)
    
    def get_total_document_count(self) -> int:
        """Get total count of documents in both raw and processed directories."""
        return self.get_local_document_count() + self.get_processed_document_count()
