import os
import logging
import json
import re
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
        Análise em múltiplas etapas para melhor qualidade com modelos pequenos.
        """
        if not self.llm_ready:
            self.connect_ollama()
        
        if not self.query_engine:
            raise ValueError("Query engine não inicializado. Execute ingest_and_index() primeiro.")

        logger.info("="*50)
        logger.info(f"MENSAGEM DO USUÁRIO: {user_text}")
        
        # Etapa 1: Classificar tipo
        tipo = self._classify_type(user_text)
        logger.info(f"TIPO CLASSIFICADO: {tipo}")
        
        # Se for CHAT, retorna resposta simples
        if tipo == "CHAT":
            resposta = self._generate_chat_response(user_text)
            result = {
                "tipo": "CHAT",
                "orgao": None,
                "resumo_qualificado": None,
                "resposta_chat": resposta
            }
            logger.info(f"RESPOSTA CHAT: {resposta}")
            logger.info("="*50)
            return json.dumps(result, ensure_ascii=False)
        
        # Etapa 2: Identificar órgão
        orgao = self._identify_organ(user_text)
        logger.info(f"ÓRGÃO IDENTIFICADO: {orgao}")
        
        # Etapa 3: Gerar resumo curto
        resumo = self._generate_summary(user_text, tipo)
        logger.info(f"RESUMO: {resumo}")
        
        # Etapa 4: Gerar descrição técnica
        resumo_tecnico = self._generate_technical_summary(user_text, tipo, orgao)
        logger.info(f"RESUMO TÉCNICO: {resumo_tecnico[:100]}...")
        
        # Etapa 5: Gerar resposta de confirmação
        resposta_confirmacao = f"Entendi. Vou classificar isso como {tipo}. Verifique os dados sugeridos abaixo."
        
        result = {
            "tipo": tipo,
            "orgao": orgao,
            "resumo": resumo,
            "resumo_qualificado": resumo_tecnico,
            "resposta_chat": resposta_confirmacao
        }
        
        logger.info("="*50)
        return json.dumps(result, ensure_ascii=False)
    
    def _classify_type(self, user_text: str) -> str:
        """Classifica o tipo da mensagem."""
        prompt = (
            f"Classifique esta mensagem em UMA categoria:\n\n"
            f"Mensagem: {user_text}\n\n"
            f"Categorias:\n"
            f"- CHAT: saudações, perguntas gerais\n"
            f"- Reclamação: problemas com serviços\n"
            f"- Denúncia: irregularidades, corrupção\n"
            f"- Solicitação: pedidos de informação ou serviços\n\n"
            f"Responda APENAS com a categoria (uma palavra):"
        )
        
        response = self.llm.complete(prompt)
        tipo = self._clean_response(response.text)
        
        # Normaliza a resposta
        if "reclamação" in tipo.lower() or "reclamacao" in tipo.lower():
            return "Reclamação"
        elif "denúncia" in tipo.lower() or "denuncia" in tipo.lower():
            return "Denúncia"
        elif "solicitação" in tipo.lower() or "solicitacao" in tipo.lower():
            return "Solicitação"
        else:
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
        """Gera fundamentação/justificativa técnica profissional."""
        prompt = (
            f"Elabore uma fundamentação breve (2-3 frases) para esta demanda:\n\n"
            f"{user_text}\n\n"
            f"Explique apenas o motivo/justificativa legal para esta {tipo.lower()}. "
            f"Use linguagem formal e objetiva. Sem JSON, sem títulos."
        )
        
        response = self.query_engine.query(prompt)
        cleaned = self._clean_response(response.response)
        
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
        
        # Limita a 300 caracteres
        if len(cleaned) > 300:
            cleaned = cleaned[:297] + "..."
        
        return cleaned.strip()
    
    def _generate_chat_response(self, user_text: str) -> str:
        """Gera resposta conversacional para CHAT."""
        prompt = (
            f"Você é o assistente da ouvidoria Fala.BR.\n"
            f"Responda de forma amigável e útil a esta mensagem:\n\n"
            f"{user_text}\n\n"
            f"Resposta:"
        )
        
        response = self.llm.complete(prompt)
        return self._clean_response(response.text)
    
    def _clean_response(self, text: str) -> str:
        """Remove markdown code blocks e limpa a resposta."""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Remove prefixos comuns
        text = text.replace("Context information is below.", "")
        text = text.replace("Given the context information", "")
        text = text.replace("Answer:", "")
        text = text.replace("Resposta:", "")
        
        # Remove informações de arquivo
        text = re.sub(r'page_label:.*?file_path:.*?\.pdf\s*', '', text, flags=re.DOTALL)
        
        # Remove aspas extras no início/fim
        text = text.strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        # Normaliza espaços mas mantém quebras de linha importantes
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = ' '.join(lines)
        
        return text
    
