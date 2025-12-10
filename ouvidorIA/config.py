from dataclasses import dataclass
import os

@dataclass
class AppConfig:
    """Configurações centrais da aplicação."""
    PAGE_TITLE: str = "Fala.BR - Assistente Inteligente"
    PAGE_ICON: str = "🗣️"
    LAYOUT: str = "wide"
    
    # --- PROVEDOR DE IA: OLLAMA (LOCAL) ---
    LLM_PROVIDER: str = "ollama" 
    
    # Ollama URL - detecta automaticamente se está no Docker ou local
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Modelo leve para computadores básicos
    # gemma2:2b = 1.6GB (mais leve, recomendado para 8GB RAM)
    # qwen2.5:1.5b = 1.5GB (ultra leve)
    # phi3:mini = 2.3GB (boa qualidade)
    OLLAMA_MODEL: str = "gemma2:2b"
    OLLAMA_TIMEOUT: float = 120.0
    
    # Embeddings locais
    EMBED_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # --- VECTOR DB (PERSISTÊNCIA) ---
    QDRANT_LOCATION: str = "./qdrant_data" 
    COLLECTION_NAME: str = "ouvidoria_knowledge"
    
    # Force rebuild da base vetorial (útil para desenvolvimento ou atualização de documentos)
    FORCE_REBUILD_INDEX: bool = os.getenv("FORCE_REBUILD_INDEX", "false").lower() == "true"
