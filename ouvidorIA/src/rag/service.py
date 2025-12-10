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
        self.llm = None
        self.llm_ready = False
        self.query_engine = None
        
        # Inicia Embeddings
        self._setup_embeddings()
        
        # Inicia Qdrant
        try:
            self.client = qdrant_client.QdrantClient(path=AppConfig.QDRANT_LOCATION)
            self.vector_store = QdrantVectorStore(client=self.client, collection_name=AppConfig.COLLECTION_NAME)
            logger.info(f"Qdrant conectado: {AppConfig.QDRANT_LOCATION}")
        except Exception as e:
            logger.error(f"Erro Qdrant: {e}")
            raise e
        
        logger.info("OuvidoriaRAGService inicializado. LLM será conectado durante indexação.")

    def _setup_embeddings(self):
        try:
            Settings.embed_model = HuggingFaceEmbedding(model_name=AppConfig.EMBED_MODEL_NAME)
        except Exception as e:
            logger.error(f"Erro Embeddings: {e}")
            raise e

    def ingest_and_index(self, uploaded_files=None, force_rebuild=False):
        try:
            # IMPORTANTE: Conecta o LLM ANTES de criar o query engine
            if not self.llm_ready:
                logger.info("Conectando Ollama antes de indexar...")
                self.connect_ollama()
            
            collection_exists = self.client.collection_exists(collection_name=AppConfig.COLLECTION_NAME)
            
            # Se force_rebuild é True, deleta o índice existente
            if force_rebuild and collection_exists:
                logger.info("Force rebuild ativado. Deletando índice existente...")
                self.client.delete_collection(collection_name=AppConfig.COLLECTION_NAME)
                collection_exists = False
                logger.info("Índice deletado. Será recriado do zero.")
                # Recria o vector_store após deletar a coleção
                self.vector_store = QdrantVectorStore(client=self.client, collection_name=AppConfig.COLLECTION_NAME)
            
            if collection_exists and not uploaded_files:
                logger.info("Índice já existe no Qdrant. Carregando sem processar PDFs...")
                index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)
                self._create_query_engine(index)
                logger.info("Query engine carregado com sucesso do índice persistido.")
                return True

            logger.info("Índice não existe ou novos arquivos foram enviados.")
            logger.info("Processando documentos via DocumentLoader...")
            documents = DocumentLoader.load_documents(uploaded_files)
            logger.info(f"DocumentLoader carregou {len(documents)} documentos.")
            
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            logger.info("Indexando documentos no Qdrant (pode demorar na primeira vez)...")
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
            self._create_query_engine(index)
            logger.info("Indexação completa. Query engine pronto.")
            return True
        except Exception as e:
            logger.error(f"Erro Indexação: {e}")
            raise e

    def connect_ollama(self):
        try:
            self.llm = Ollama(
                model=AppConfig.OLLAMA_MODEL, 
                base_url=AppConfig.OLLAMA_BASE_URL,
                request_timeout=AppConfig.OLLAMA_TIMEOUT,
                temperature=0.1, 
                json_mode=False 
            )
            Settings.llm = self.llm
            self.llm_ready = True
            logger.info(f"Ollama conectado: {AppConfig.OLLAMA_MODEL} @ {AppConfig.OLLAMA_BASE_URL}")
        except Exception as e:
            self.llm_ready = False
            logger.error(f"Erro ao conectar Ollama: {e}")
            raise e

    def _create_query_engine(self, index):
        from llama_index.core.prompts import PromptTemplate
        
        # Verifica se LLM está configurado
        if not self.llm_ready or Settings.llm is None:
            raise ValueError("LLM não está conectado. Chame connect_ollama() primeiro.")
        
        logger.info(f"Criando query engine com LLM: {Settings.llm.__class__.__name__}")
        
        # Template simplificado
        qa_prompt = PromptTemplate(
            "Contexto: {context_str}\n\n"
            "Pergunta: {query_str}\n\n"
            "Resposta (apenas JSON):"
        )
        
        self.query_engine = index.as_query_engine(
            similarity_top_k=2,
            text_qa_template=qa_prompt,
            response_mode="compact",
            llm=self.llm  # Passa explicitamente o LLM
        )

    def query(self, prompt: str):
        if not self.llm_ready:
            self.connect_ollama()
        if not self.query_engine:
            raise ValueError("Query engine não inicializado. Execute ingest_and_index() primeiro.")
        return self.query_engine.query(prompt)
    
    def get_index_info(self):
        """Retorna informações sobre o índice carregado."""
        try:
            collection_info = self.client.get_collection(AppConfig.COLLECTION_NAME)
            return {
                "exists": True,
                "vectors_count": collection_info.vectors_count if hasattr(collection_info, 'vectors_count') else "N/A"
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}

    def analyze_demand(self, user_text: str):
        """
        Roteador Inteligente com RAG:
        Usa a base de conhecimento (PDFs da ouvidoria) para analisar a demanda.
        """
        if not self.llm_ready:
            self.connect_ollama()
        
        if not self.query_engine:
            raise ValueError("Query engine não inicializado. Execute ingest_and_index() primeiro.")

        # Prompt simplificado para modelos menores
        analysis_prompt = (
            f"Analise esta mensagem e retorne um JSON.\n\n"
            f"Mensagem: {user_text}\n\n"
            f"Retorne no formato:\n"
            f'{{"tipo": "CHAT ou Reclamação ou Denúncia ou Solicitação", '
            f'"orgao": "nome do órgão ou null", '
            f'"resumo_qualificado": "texto técnico ou null", '
            f'"resposta_chat": "sua resposta"}}'
        )

        # Usa RAG para consultar a base de conhecimento
        response = self.query_engine.query(analysis_prompt)
        raw_response = response.response
        
        # Log da resposta completa para debug
        logger.info("="*50)
        logger.info(f"MENSAGEM DO USUÁRIO: {user_text}")
        logger.info(f"RESPOSTA RAG (primeiros 500 chars): {raw_response[:500]}")
        
        # Tenta extrair apenas o JSON da resposta
        cleaned_response = self._extract_json_from_response(raw_response)
        logger.info(f"RESPOSTA LIMPA: {cleaned_response[:300]}")
        logger.info("="*50)
        
        return cleaned_response
    
    def _extract_json_from_response(self, response: str) -> str:
        """
        Extrai apenas o JSON da resposta, removendo contexto extra.
        """
        import re
        
        # Tenta encontrar um objeto JSON na resposta
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            logger.info(f"JSON encontrado via regex: {json_str[:200]}")
            return json_str
        
        # Fallback: remove apenas o contexto mais óbvio
        response = response.replace("Context information is below.", "")
        response = re.sub(r'page_label:.*?file_path:.*?\.pdf\s*', '', response, flags=re.DOTALL)
        response = re.sub(r'Given the context information.*?Query:', '', response, flags=re.DOTALL)
        response = response.replace("Answer:", "").strip()
        
        # Procura por { e pega dali até o }
        start = response.find('{')
        if start >= 0:
            end = response.rfind('}')
            if end > start:
                cleaned = response[start:end+1]
                logger.info(f"JSON encontrado por busca manual: {cleaned[:200]}")
                return cleaned
        
        logger.warning("Nenhum JSON encontrado na resposta. Retornando resposta original.")
        return response
