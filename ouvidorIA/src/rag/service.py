import os
import logging
import json
import qdrant_client
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.ollama import Ollama

from config import AppConfig
from src.etl.loader import DocumentLoader

logger = logging.getLogger(__name__)

class OuvidoriaRAGService:
    def __init__(self):
        # 1. Bloqueia OpenAI padrão
        Settings.llm = None
        
        # 2. Inicia Embeddings e Qdrant
        self._setup_embeddings()
        try:
            self.client = qdrant_client.QdrantClient(path=AppConfig.QDRANT_LOCATION)
            self.vector_store = QdrantVectorStore(client=self.client, collection_name=AppConfig.COLLECTION_NAME)
            logger.info(f"Qdrant conectado: {AppConfig.QDRANT_LOCATION}")
        except Exception as e:
            logger.error(f"Erro Qdrant: {e}")
            raise e

        self.query_engine = None
        self.llm_ready = False

    def _setup_embeddings(self):
        try:
            Settings.embed_model = HuggingFaceEmbedding(model_name=AppConfig.EMBED_MODEL_NAME)
        except Exception as e:
            logger.error(f"Erro Embeddings: {e}")
            raise e

    def ingest_and_index(self, uploaded_files=None):
        try:
            collection_exists = self.client.collection_exists(collection_name=AppConfig.COLLECTION_NAME)
            
            if collection_exists and not uploaded_files:
                logger.info("Carregando índice existente...")
                index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)
                self._create_query_engine(index)
                return True

            logger.info("Criando índice...")
            documents = DocumentLoader.load_documents(uploaded_files)
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
            self._create_query_engine(index)
            return True
        except Exception as e:
            logger.error(f"Erro Indexação: {e}")
            raise e

    def connect_ollama(self):
        try:
            llm = Ollama(
                model=AppConfig.OLLAMA_MODEL, 
                base_url=AppConfig.OLLAMA_BASE_URL,
                request_timeout=AppConfig.OLLAMA_TIMEOUT,
                temperature=0.1, 
                json_mode=False 
            )
            Settings.llm = llm
            self.llm_ready = True
        except Exception as e:
            self.llm_ready = False
            raise e

    def _create_query_engine(self, index):
        self.query_engine = index.as_query_engine(similarity_top_k=3)

    def query(self, prompt: str):
        if not self.llm_ready:
            self.connect_ollama()
        return self.query_engine.query(prompt)

    def analyze_demand(self, user_text: str):
        """
        Roteador Inteligente:
        Decide se é papo furado (CHAT) ou trabalho sério (JSON de Formulário).
        """
        if not self.llm_ready:
            self.connect_ollama()

        # Prompt com Roteamento Explicito
        analysis_prompt = (
            "Você é o OuvidorIA, assistente oficial do Fala.BR.\n"
            "Sua missão: Analisar a mensagem do cidadão.\n\n"
            "REGRAS DE DECISÃO:\n"
            "1. Se for SAUDAÇÃO (ex: 'oi', 'olá', 'bom dia') ou pergunta genérica fora do contexto: Classifique como 'CHAT'.\n"
            "2. Se for um RELATO DE PROBLEMA, DENÚNCIA ou DÚVIDA TÉCNICA: Classifique como 'Solicitação', 'Reclamação', etc.\n\n"
            "Retorne APENAS um JSON neste formato:\n"
            "{\n"
            '  "tipo": "CHAT" ou "Solicitação" | "Reclamação" | "Denúncia",\n'
            '  "orgao": "Nome do Órgão" (ou null se for CHAT),\n'
            '  "resumo_qualificado": "Texto técnico reescrito" (ou null se for CHAT),\n'
            '  "resposta_chat": "Sua resposta cordial falando diretamente com o usuário"\n'
            "}\n"
            "---------------------\n"
            f"MENSAGEM DO CIDADÃO: {user_text}\n"
        )
        
        response = self.query_engine.query(analysis_prompt)
        return response.response
