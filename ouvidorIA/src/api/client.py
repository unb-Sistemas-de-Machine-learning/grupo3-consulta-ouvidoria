"""
Client for communicating with the FastAPI backend.
Used by the Streamlit frontend to call the API.
Supports both sync and async requests.
"""
import requests
import httpx
import asyncio
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class OuvidoriaAPIClient:
    """Client for OuvidorIA FastAPI backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self._async_client: Optional[httpx.AsyncClient] = None
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    def ingest_documents(
        self,
        force_rebuild: bool = False,
        files: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest and index documents.
        
        Args:
            force_rebuild: Whether to rebuild the index from scratch
            files: Optional list of uploaded files (Streamlit UploadedFile objects)
        
        Returns:
            Response dict with success status and message
        """
        try:
            url = f"{self.base_url}/api/ingest"
            params = {"force_rebuild": force_rebuild}
            
            if files:
                # Prepare files for multipart/form-data
                file_data = []
                for file in files:
                    file_data.append(
                        ("files", (file.name, file.getvalue(), file.type))
                    )
                
                response = self.session.post(
                    url,
                    params=params,
                    files=file_data,
                    timeout=300  # Long timeout for document processing
                )
            else:
                response = self.session.post(
                    url,
                    params=params,
                    timeout=300
                )
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")
            raise
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the current index."""
        try:
            response = self.session.get(f"{self.base_url}/api/index/info", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting index info: {e}")
            raise
    
    def query(self, prompt: str) -> str:
        """
        Query the RAG system.
        
        Args:
            prompt: The query prompt
        
        Returns:
            Response text
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/query",
                json={"prompt": prompt},
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Error querying: {e}")
            raise
    
    def analyze_demand(self, user_text: str) -> Dict[str, Any]:
        """
        Analyze a user demand and return structured information.
        
        Args:
            user_text: The user's message/demand
        
        Returns:
            Dict with tipo, orgao, resumo, resumo_qualificado, resposta_chat
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/analyze",
                json={"user_text": user_text},
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error analyzing demand: {e}")
            raise
    
    async def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=120.0)
        return self._async_client
    
    async def analyze_demand_async(self, user_text: str) -> Dict[str, Any]:
        """
        Analyze a user demand asynchronously.
        
        Args:
            user_text: The user's message/demand
        
        Returns:
            Dict with tipo, orgao, resumo, resumo_qualificado, resposta_chat
        """
        try:
            client = await self._get_async_client()
            response = await client.post(
                f"{self.base_url}/api/analyze",
                json={"user_text": user_text},
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error analyzing demand (async): {e}")
            raise
    
    async def get_index_info_async(self) -> Dict[str, Any]:
        """Get information about the current index (async)."""
        try:
            client = await self._get_async_client()
            response = await client.get(f"{self.base_url}/api/index/info", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting index info (async): {e}")
            raise
    
    async def health_check_async(self) -> Dict[str, Any]:
        """Check if the API is healthy (async)."""
        try:
            client = await self._get_async_client()
            response = await client.get(f"{self.base_url}/health", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed (async): {e}")
            raise
    
    async def close_async_client(self):
        """Close the async HTTP client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
    
    def __del__(self):
        """Cleanup async client on destruction."""
        if self._async_client:
            try:
                # Try to close in a new event loop if one doesn't exist
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule close
                    asyncio.create_task(self._async_client.aclose())
                else:
                    loop.run_until_complete(self._async_client.aclose())
            except RuntimeError:
                # No event loop, create one
                asyncio.run(self._async_client.aclose())
