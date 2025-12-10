from dataclasses import dataclass

@dataclass
class AppConfig:
    """Configurações centrais da aplicação."""
    PAGE_TITLE: str = "Fala.BR - Assistente Inteligente"
    PAGE_ICON: str = "🗣️"
    LAYOUT: str = "wide"
    
    # --- PROVEDOR DE IA: OLLAMA (LOCAL) ---
    LLM_PROVIDER: str = "ollama" 
    
    # Seu servidor na rede local
    OLLAMA_BASE_URL: str = "http://10.0.0.10:11434"
    
    # Modelo baixado no servidor
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: float = 120.0
    
    # Embeddings locais
    EMBED_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # --- VECTOR DB (PERSISTÊNCIA) ---
    # Mudamos de ":memory:" para um caminho local para salvar os dados
    QDRANT_LOCATION: str = "./qdrant_data" 
    COLLECTION_NAME: str = "ouvidoria_knowledge"
