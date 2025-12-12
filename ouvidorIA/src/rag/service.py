import os
import logging
import re
import qdrant_client
from typing import List, Dict, Any, Optional
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.ollama import Ollama

from config import AppConfig
from src.etl.loader import DocumentLoader, FileWrapper
from src.rag.exceptions import (
    LLMConnectionError,
    QueryEngineNotReadyError,
    IndexNotReadyError,
    IndexingError
)

logger = logging.getLogger(__name__)

class OuvidoriaRAGService:
    """
    RAG Service for OuvidorIA.
    Handles document indexing, querying, and demand analysis.
    """
    
    def __init__(self, document_loader: Optional[DocumentLoader] = None):
        """
        Initialize RAG Service.
        
        Args:
            document_loader: Optional DocumentLoader instance. If None, creates a new one.
        """
        self.llm = None
        self.llm_ready = False
        self.query_engine = None
        
        # Initialize document loader
        self.document_loader = document_loader or DocumentLoader()
        
        # Initialize embeddings
        self._setup_embeddings()
        
        # Initialize Qdrant
        try:
            self.client = qdrant_client.QdrantClient(path=AppConfig.QDRANT_LOCATION)
            self.vector_store = QdrantVectorStore(
                client=self.client, 
                collection_name=AppConfig.COLLECTION_NAME
            )
            logger.info(f"Qdrant connected: {AppConfig.QDRANT_LOCATION}")
        except Exception as e:
            logger.error(f"Qdrant connection error: {e}")
            raise IndexNotReadyError(f"Failed to connect to Qdrant: {e}") from e
        
        logger.info("OuvidoriaRAGService initialized. LLM will be connected during indexing.")
    
    def is_ready(self) -> bool:
        """Check if the service is fully ready (LLM connected and query engine available)."""
        return self.llm_ready and self.query_engine is not None
    
    def load_existing_index(self) -> bool:
        """
        Load existing index if it exists without rebuilding.
        Returns True if index was loaded, False otherwise.
        """
        try:
            from llama_index.core import VectorStoreIndex
            from config import AppConfig
            
            collection_exists = self.client.collection_exists(collection_name=AppConfig.COLLECTION_NAME)
            if not collection_exists:
                logger.info("No existing collection found.")
                return False
            
            # Ensure LLM is ready before creating query engine
            try:
                self._ensure_llm_ready()
            except Exception as e:
                logger.warning(f"Could not connect LLM: {e}. Index will be loaded but query engine will be created later.")
                return False
            
            logger.info("Loading existing index from Qdrant...")
            index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)
            self._create_query_engine(index)
            logger.info("Existing index loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Error loading existing index: {e}")
            return False

    def _setup_embeddings(self):
        try:
            Settings.embed_model = HuggingFaceEmbedding(model_name=AppConfig.EMBED_MODEL_NAME)
        except Exception as e:
            logger.error(f"Erro Embeddings: {e}")
            raise e

    def ingest_and_index(
        self, 
        uploaded_files: Optional[List[FileWrapper]] = None, 
        force_rebuild: bool = False
    ) -> Dict[str, Any]:
        """
        Ingest and index documents.
        
        Args:
            uploaded_files: Optional list of FileWrapper objects to index
            force_rebuild: If True, delete existing index and rebuild from scratch
        
        Returns:
            Dict with indexing results: {'success': bool, 'documents_count': int, 'rebuilt': bool}
        
        Raises:
            IndexingError: If indexing fails
            LLMConnectionError: If LLM connection fails
        """
        try:
            # Ensure LLM is connected before creating query engine
            self._ensure_llm_ready()
            
            collection_exists = self.client.collection_exists(
                collection_name=AppConfig.COLLECTION_NAME
            )
            
            # If force_rebuild is True, delete existing index
            if force_rebuild and collection_exists:
                logger.info("Force rebuild enabled. Deleting existing index...")
                self.client.delete_collection(collection_name=AppConfig.COLLECTION_NAME)
                collection_exists = False
                logger.info("Index deleted. Will be recreated from scratch.")
                # Recreate vector_store after deleting collection
                self.vector_store = QdrantVectorStore(
                    client=self.client, 
                    collection_name=AppConfig.COLLECTION_NAME
                )
            
            # If index exists and no new files, just load it
            if collection_exists and not uploaded_files:
                logger.info("Index already exists in Qdrant. Loading without processing PDFs...")
                index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)
                self._create_query_engine(index)
                logger.info("Query engine loaded successfully from persisted index.")
                
                index_info = self.get_index_info()
                return {
                    'success': True,
                    'documents_count': index_info.get('vectors_count', 0),
                    'rebuilt': False,
                    'message': 'Index loaded from existing collection'
                }

            # Index doesn't exist or new files were provided - process documents
            logger.info("Index doesn't exist or new files provided. Processing documents...")
            documents = self.document_loader.load_documents(uploaded_files)
            logger.info(f"DocumentLoader loaded {len(documents)} document chunks.")
            
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            logger.info("Indexing documents in Qdrant (may take time on first run)...")
            index = VectorStoreIndex.from_documents(
                documents, 
                storage_context=storage_context
            )
            self._create_query_engine(index)
            logger.info("Indexing complete. Query engine ready.")
            
            index_info = self.get_index_info()
            return {
                'success': True,
                'documents_count': index_info.get('vectors_count', len(documents)),
                'rebuilt': force_rebuild,
                'message': 'Documents indexed successfully'
            }
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            raise IndexingError(f"Failed to index documents: {e}") from e

    def connect_ollama(self) -> None:
        """
        Connect to Ollama LLM service.
        
        Raises:
            LLMConnectionError: If connection fails
        """
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
            logger.info(
                f"Ollama connected: {AppConfig.OLLAMA_MODEL} @ {AppConfig.OLLAMA_BASE_URL}"
            )
        except Exception as e:
            self.llm_ready = False
            logger.error(f"Error connecting to Ollama: {e}")
            raise LLMConnectionError(f"Failed to connect to Ollama: {e}") from e

    def _create_query_engine(self, index):
        from llama_index.core.prompts import PromptTemplate
        
        # Verifica se LLM está configurado
        if not self.llm_ready or Settings.llm is None:
            raise ValueError("LLM não está conectado. Chame connect_ollama() primeiro.")
        
        logger.info(f"Criando query engine com LLM: {Settings.llm.__class__.__name__}")
        
        # Template para respostas em texto simples (não JSON)
        qa_prompt = PromptTemplate(
            "Você é um assistente especializado em ouvidoria pública.\n\n"
            "Contexto dos documentos:\n{context_str}\n\n"
            "Pergunta: {query_str}\n\n"
            "Resposta (texto simples, sem JSON, sem markdown, sem códigos):"
        )
        
        self.query_engine = index.as_query_engine(
            similarity_top_k=2,
            text_qa_template=qa_prompt,
            response_mode="compact",
            llm=self.llm  # Passa explicitamente o LLM
        )

    def _ensure_llm_ready(self) -> None:
        """
        Ensure LLM is connected, connecting if necessary.
        
        Raises:
            LLMConnectionError: If connection fails
        """
        if not self.llm_ready:
            logger.info("LLM not ready. Attempting to connect...")
            self.connect_ollama()
    
    def _ensure_query_engine(self) -> None:
        """
        Ensure query engine is ready.
        
        Raises:
            QueryEngineNotReadyError: If query engine is not initialized
        """
        if not self.query_engine:
            raise QueryEngineNotReadyError(
                "Query engine not initialized. Please run ingest_and_index() first."
            )
    
    def query(self, prompt: str) -> str:
        """
        Query the RAG system.
        
        Args:
            prompt: Query prompt
        
        Returns:
            Response string from the query engine
        
        Raises:
            QueryEngineNotReadyError: If query engine is not initialized
            LLMConnectionError: If LLM connection fails
        """
        self._ensure_llm_ready()
        if not self.query_engine:
            raise QueryEngineNotReadyError(
                "Query engine not initialized. Please run ingest_and_index() first."
            )
        response = self.query_engine.query(prompt)
        return str(response)
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        Get information about the current index.
        
        Returns:
            Dict with index information: {'exists': bool, 'vectors_count': int, 'error': Optional[str]}
        """
        try:
            collection_info = self.client.get_collection(AppConfig.COLLECTION_NAME)
            
            # Qdrant CollectionInfo has points_count attribute
            # points_count = number of points (vectors with payloads) in the collection
            vectors_count = collection_info.points_count
            
            logger.info(f"Collection points_count: {vectors_count}")
            
            return {
                "exists": True,
                "vectors_count": vectors_count
            }
        except Exception as e:
            logger.warning(f"Could not get collection info: {e}")
            return {"exists": False, "vectors_count": 0, "error": str(e)}

    def analyze_demand(self, user_text: str) -> Dict[str, Any]:
        """
        Analyze user demand in multiple steps for better quality with small models.
        Returns a dict (not JSON string) for better API integration.
        
        Args:
            user_text: User's message/demand text
        
        Returns:
            Dict with analysis results:
            {
                'tipo': str,
                'orgao': Optional[str],
                'resumo': Optional[str],
                'resumo_qualificado': Optional[str],
                'resposta_chat': str
            }
        
        Raises:
            QueryEngineNotReadyError: If query engine is not initialized
            LLMConnectionError: If LLM connection fails
        """
        self._ensure_llm_ready()
        
        if not self.query_engine:
            raise QueryEngineNotReadyError(
                "Query engine not initialized. Please run ingest_and_index() first."
            )

        logger.info("="*50)
        logger.info(f"USER MESSAGE: {user_text}")
        
        # Step 1: Classify type
        tipo = self._classify_type(user_text)
        logger.info(f"CLASSIFIED TYPE: {tipo}")
        
        # If CHAT, return simple response
        if tipo == "CHAT":
            resposta = self._generate_chat_response(user_text)
            result = {
                "tipo": "CHAT",
                "orgao": None,
                "resumo": None,
                "resumo_qualificado": None,
                "resposta_chat": resposta
            }
            logger.info(f"CHAT RESPONSE: {resposta}")
            logger.info("="*50)
            return result
        
        # Step 2: Identify organ
        orgao = self._identify_organ(user_text)
        logger.info(f"IDENTIFIED ORGAN: {orgao}")
        
        # Step 3: Generate short summary
        resumo = self._generate_summary(user_text, tipo)
        logger.info(f"SUMMARY: {resumo}")
        
        # Step 4: Generate technical description
        resumo_tecnico = self._generate_technical_summary(user_text, tipo, orgao)
        logger.info(f"TECHNICAL SUMMARY: {resumo_tecnico[:100]}...")
        
        # Step 5: Generate confirmation response
        resposta_confirmacao = (
            f"Entendi. Vou classificar isso como {tipo}. "
            f"Verifique os dados sugeridos abaixo."
        )
        
        result = {
            "tipo": tipo,
            "orgao": orgao,
            "resumo": resumo,
            "resumo_qualificado": resumo_tecnico,
            "resposta_chat": resposta_confirmacao
        }
        
        logger.info("="*50)
        return result
    
    def _classify_type(self, user_text: str) -> str:
        """Classifica o tipo da mensagem usando LLM."""
        self._ensure_llm_ready()
        
        prompt = (
            f"Classifique esta mensagem em UMA categoria:\n\n"
            f"Mensagem: {user_text}\n\n"
            f"Categorias:\n"
            f"- CHAT: saudações, perguntas gerais, conversas casuais\n"
            f"- Reclamação: problemas com serviços públicos\n"
            f"- Denúncia: irregularidades, corrupção, fraudes\n"
            f"- Solicitação: pedidos de informação ou serviços\n\n"
            f"Responda APENAS com a categoria (uma palavra, sem JSON, sem explicações):"
        )
        
        response = self.llm.complete(prompt)
        tipo = self._clean_response(response.text)
        logger.info(f"CLASSIFIED TYPE (raw): {response.text}, (cleaned): {tipo}")
                
        # Extract just the category word
        tipo = tipo.strip().split()[0] if tipo.strip().split() else tipo.strip()
        
        # Normaliza a resposta
        tipo_lower = tipo.lower()
        if "reclamação" in tipo_lower or "reclamacao" in tipo_lower or "reclamacao" in tipo_lower:
            return "Reclamação"
        elif "denúncia" in tipo_lower or "denuncia" in tipo_lower:
            return "Denúncia"
        elif "solicitação" in tipo_lower or "solicitacao" in tipo_lower:
            return "Solicitação"
        else:
            # Default to CHAT for anything else (safer for simple messages)
            return "CHAT"
    
    def _identify_organ(self, user_text: str) -> str:
        """Identifica o órgão responsável usando RAG."""
        prompt = (
            f"Qual órgão público é responsável por esta demanda?\n\n"
            f"{user_text}\n\n"
            f"Escolha um: Ministério da Saúde (MS), Ministério da Educação (MEC), "
            f"Controladoria-Geral da União (CGU), INSS, Polícia Federal (PF), Receita Federal (RFB).\n"
            f"Responda apenas com o nome:"
        )
        
        response = self.query_engine.query(prompt)
        orgao = self._clean_response(response.response)
        
        # Se a resposta for muito longa, pega só as primeiras palavras
        if len(orgao) > 100:
            orgao = " ".join(orgao.split()[:6])
        
        # Normaliza nomes comuns
        orgao_lower = orgao.lower()
        if "saúde" in orgao_lower or "saude" in orgao_lower or "sus" in orgao_lower:
            return "Ministério da Saúde (MS)"
        elif "educação" in orgao_lower or "educacao" in orgao_lower or "mec" in orgao_lower:
            return "Ministério da Educação (MEC)"
        elif "cgu" in orgao_lower or "controladoria" in orgao_lower:
            return "Controladoria-Geral da União (CGU)"
        elif "inss" in orgao_lower or "previdência" in orgao_lower or "previdencia" in orgao_lower:
            return "Instituto Nacional do Seguro Social (INSS)"
        elif "polícia federal" in orgao_lower or "policia federal" in orgao_lower or " pf" in orgao_lower:
            return "Polícia Federal (PF)"
        elif "receita" in orgao_lower or "rfb" in orgao_lower:
            return "Receita Federal (RFB)"
        
        return orgao if orgao else "Órgão não identificado"
    
    def _generate_summary(self, user_text: str, tipo: str) -> str:
        """Gera um resumo curto (1 frase) da demanda."""
        self._ensure_llm_ready()
        
        prompt = (
            f"Resuma esta mensagem em UMA frase curta e direta:\n\n"
            f"{user_text}\n\n"
            f"Responda apenas com o resumo (máximo 10 palavras):"
        )
        
        response = self.llm.complete(prompt)
        resumo = self._clean_response(response.text)
        
        # Limita a 100 caracteres
        if len(resumo) > 100:
            resumo = resumo[:97] + "..."
        
        return resumo.strip()
    
    def _generate_technical_summary(self, user_text: str, tipo: str, orgao: str) -> str:
        """Gera fundamentação/justificativa técnica profissional usando RAG."""
        self._ensure_query_engine()
        
        # Prompt melhorado para usar o RAG e buscar contexto relevante
        prompt = (
            f"Com base nos documentos e regulamentações disponíveis, elabore uma fundamentação técnica breve (2-3 frases) "
            f"para esta demanda de {tipo.lower()} relacionada ao {orgao}:\n\n"
            f"Demanda do cidadão: {user_text}\n\n"
            f"Instruções:\n"
            f"- Use informações dos documentos e leis disponíveis no contexto\n"
            f"- Explique o motivo/justificativa legal ou técnica para esta {tipo.lower()}\n"
            f"- Use linguagem formal, objetiva e profissional\n"
            f"- Responda APENAS com o texto da fundamentação, sem JSON, sem markdown, sem títulos, sem códigos\n"
            f"- Se não houver informação relevante no contexto, explique brevemente a natureza da {tipo.lower()}"
        )
        
        try:
            logger.info(f"Querying RAG for technical summary (tipo: {tipo}, orgao: {orgao})")
            response = self.query_engine.query(prompt)
            
            if not response or not response.response:
                logger.warning("Empty response from query_engine, generating fallback")
                # Fallback: gera uma fundamentação básica sem RAG
                return self._generate_fallback_technical_summary(user_text, tipo, orgao)
            
            cleaned = self._clean_response(response.response)
            logger.info(f"Raw technical summary response: {response.response[:200]}...")
            
            # Remove estruturas JSON se ainda existirem
            if '{' in cleaned and '}' in cleaned:
                # Tenta extrair apenas o texto útil do JSON
                json_match = re.search(r'"response":\s*"([^"]+)"', cleaned)
                if json_match:
                    cleaned = json_match.group(1)
                else:
                    # Remove chaves e deixa só o texto
                    cleaned = re.sub(r'[{}]', '', cleaned)
                    cleaned = re.sub(r'"[^"]+"\s*:\s*"', '', cleaned)
                    cleaned = cleaned.replace('"', '')
            
            # Remove markdown se existir
            cleaned = re.sub(r'```[^`]*```', '', cleaned)
            cleaned = re.sub(r'`[^`]*`', '', cleaned)
            cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # Remove bold
            cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)  # Remove italic
            
            # Limpa espaços extras
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            # Se ainda estiver vazio após limpeza, usa fallback
            if not cleaned or len(cleaned.strip()) < 10:
                logger.warning("Technical summary too short after cleaning, using fallback")
                return self._generate_fallback_technical_summary(user_text, tipo, orgao)
            
            # Limita a 300 caracteres
            if len(cleaned) > 300:
                cleaned = cleaned[:297] + "..."
            
            logger.info(f"Final technical summary: {cleaned[:100]}...")
            return cleaned.strip()
            
        except Exception as e:
            logger.error(f"Error generating technical summary with RAG: {e}", exc_info=True)
            # Fallback em caso de erro
            return self._generate_fallback_technical_summary(user_text, tipo, orgao)
    
    def _generate_fallback_technical_summary(self, user_text: str, tipo: str, orgao: str) -> str:
        """Gera fundamentação básica quando o RAG não retorna resultado."""
        self._ensure_llm_ready()
        
        prompt = (
            f"Elabore uma fundamentação técnica breve (2-3 frases) para esta {tipo.lower()} "
            f"relacionada ao {orgao}:\n\n"
            f"{user_text}\n\n"
            f"Explique o motivo/justificativa legal ou técnica. Use linguagem formal e objetiva. "
            f"Responda APENAS com o texto, sem JSON, sem markdown."
        )
        
        try:
            response = self.llm.complete(prompt)
            cleaned = self._clean_response(response.text)
            
            # Limita a 300 caracteres
            if len(cleaned) > 300:
                cleaned = cleaned[:297] + "..."
            
            return cleaned.strip()
        except Exception as e:
            logger.error(f"Error in fallback technical summary: {e}")
            # Último recurso: retorna uma fundamentação genérica
            return f"Fundamentação técnica para {tipo.lower()} relacionada ao {orgao} conforme regulamentação aplicável."
    
    def _generate_chat_response(self, user_text: str) -> str:
        """Gera resposta conversacional para CHAT usando LLM."""
        self._ensure_llm_ready()
        
        prompt = (
            f"Você é o assistente da ouvidoria Fala.BR.\n"
            f"Responda de forma amigável e breve (máximo 2 frases).\n"
            f"IMPORTANTE: Responda APENAS com texto simples, sem JSON, sem markdown, sem código.\n"
            f"Não use estruturas JSON. Não use ``` ou markdown.\n"
            f"Seja direto e objetivo.\n\n"
            f"Mensagem do usuário: {user_text}\n\n"
            f"Sua resposta (apenas texto simples):"
        )
        
        try:
            response = self.llm.complete(prompt)
            cleaned = self._clean_response(response.text)
            
            # Aggressive cleaning for chat responses
            # Remove any JSON structures
            cleaned = re.sub(r'\{[^{}]*"resposta"[^{}]*:?\s*"([^"]*)"[^{}]*\}', r'\1', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'\{[^{}]*\}', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'```json.*?```', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
            
            # If response is still too long or contains JSON-like structures, use fallback
            if len(cleaned) > 150 or ('{' in cleaned and '}' in cleaned) or len(cleaned.split('.')) > 3:
                logger.warning(f"Chat response too long or contains JSON. Using fallback. Original length: {len(cleaned)}")
                return "Olá! Como posso ajudá-lo com sua demanda na ouvidoria?"
            
            return cleaned.strip() if cleaned.strip() else "Olá! Como posso ajudá-lo?"
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return "Olá! Como posso ajudá-lo com sua demanda na ouvidoria?"
    
    def _clean_response(self, text: str) -> str:
        """Remove markdown code blocks e limpa a resposta."""
        if not text:
            return ""
        
        # First, try to extract JSON content if present
        # Handle nested JSON in markdown code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                import json
                json_str = json_match.group(1)
                json_obj = json.loads(json_str)
                # Extract "response" field if it exists
                if isinstance(json_obj, dict) and "response" in json_obj:
                    text = json_obj["response"]
                elif isinstance(json_obj, dict) and "resposta" in json_obj:
                    text = json_obj["resposta"]
                else:
                    # If no response/resposta field, convert dict to string
                    text = str(json_obj)
            except (json.JSONDecodeError, KeyError, ValueError):
                # If JSON parsing fails, continue with original text
                pass
        
        # Also try to extract JSON without markdown wrapper
        json_match_no_md = re.search(r'\{[^{}]*"response"[^{}]*:?\s*"((?:[^"\\]|\\.)*)"[^{}]*\}', text, re.DOTALL)
        if json_match_no_md:
            try:
                import json
                # Try to parse the whole JSON object
                full_json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if full_json_match:
                    json_str = full_json_match.group(0)
                    json_obj = json.loads(json_str)
                    if isinstance(json_obj, dict) and "response" in json_obj:
                        text = json_obj["response"]
                    elif isinstance(json_obj, dict) and "resposta" in json_obj:
                        text = json_obj["resposta"]
            except (json.JSONDecodeError, KeyError, ValueError):
                # Extract just the value using regex
                text = json_match_no_md.group(1)
                text = text.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
        
        # Remove markdown code blocks (all variations)
        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        text = re.sub(r'`[^`]*`', '', text)  # Remove inline code
        
        # Try to extract JSON "response" or "resposta" field value
        # Handle escaped quotes and newlines in JSON strings
        response_match = re.search(r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
        if response_match:
            text = response_match.group(1)
            # Unescape JSON string
            text = text.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
        
        resposta_match = re.search(r'"resposta"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
        if resposta_match:
            text = resposta_match.group(1)
            # Unescape JSON string
            text = text.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
        
        # Remove JSON structures (more aggressive)
        text = re.sub(r'\{[^{}]*"response"[^{}]*:?\s*"([^"]*)"[^{}]*\}', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'\{[^{}]*"resposta"[^{}]*:?\s*"([^"]*)"[^{}]*\}', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'\{[^{}]*\}', '', text, flags=re.DOTALL)
        
        # Remove prefixos comuns
        text = text.replace("Context information is below.", "")
        text = text.replace("Given the context information", "")
        text = text.replace("Answer:", "")
        text = text.replace("Resposta:", "")
        text = text.replace("Resposta (apenas texto):", "")
        
        # Remove informações de arquivo/metadata
        text = re.sub(r'page_label:.*?file_path:.*?\.pdf\s*', '', text, flags=re.DOTALL)
        text = re.sub(r'file_path:.*?\.pdf', '', text, flags=re.DOTALL)
        
        # Remove aspas extras no início/fim
        text = text.strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
        
        # Remove any remaining JSON-like structures
        text = re.sub(r'"response"\s*:\s*"', '', text)
        text = re.sub(r'"resposta"\s*:\s*"', '', text)
        text = re.sub(r'^\s*[\{\[]\s*', '', text)  # Remove leading { or [
        text = re.sub(r'\s*[\}\]]\s*$', '', text)  # Remove trailing } or ]
        
        # Normaliza espaços mas mantém quebras de linha importantes
        lines = [line.strip() for line in text.split('\n') if line.strip() and not line.strip().startswith('{') and not line.strip().startswith('[')]
        text = ' '.join(lines)
        
        # Final cleanup - remove any remaining special characters that might be JSON
        text = text.strip()
        
        return text
    
