import os
import shutil
from typing import List, Any, Optional
from llama_index.core import Document, SimpleDirectoryReader
import logging

# Configura logger para podermos ver o que está acontecendo no terminal
logger = logging.getLogger(__name__)

class DocumentLoader:
    """
    Responsável pela ingestão de dados.
    Política de Leitura: Prioriza Uploads da Interface > Pasta Local 'data/raw'.
    """

    LOCAL_DATA_DIR = os.path.join("data", "raw")
    TEMP_DIR = "temp_data"

    @staticmethod
    def load_documents(uploaded_files: Optional[List[Any]] = None) -> List[Document]:
        """
        Carrega documentos disponíveis.
        Lança ValueError se nenhuma fonte de dados for encontrada.
        """
        logger.info("=" * 50)
        logger.info("DocumentLoader.load_documents() CHAMADO")
        logger.info("=" * 50)

        # 1. Estratégia: Arquivos enviados pelo usuário (Upload)
        if uploaded_files:
            logger.info(f"Estratégia: Upload de usuário ({len(uploaded_files)} arquivos)")
            return DocumentLoader._process_uploads(uploaded_files)

        # 2. Estratégia: Arquivos locais na pasta data/raw
        if DocumentLoader._local_data_exists():
            file_count = len(os.listdir(DocumentLoader.LOCAL_DATA_DIR))
            logger.info(f"Estratégia: Arquivos locais em '{DocumentLoader.LOCAL_DATA_DIR}' ({file_count} arquivos)")
            documents = SimpleDirectoryReader(DocumentLoader.LOCAL_DATA_DIR).load_data()
            logger.info(f"Documentos carregados: {len(documents)} chunks de texto")
            return documents
 
        # 3. Falha: Nenhum dado encontrado (Sem Mocks)
        error_msg = (
            f"Nenhum documento encontrado! Por favor, faça upload na interface "
            f"ou adicione arquivos (.pdf, .txt) na pasta '{DocumentLoader.LOCAL_DATA_DIR}'."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    @staticmethod
    def _local_data_exists() -> bool:
        """Verifica se a pasta local existe e não está vazia."""
        return (os.path.exists(DocumentLoader.LOCAL_DATA_DIR) and 
                len(os.listdir(DocumentLoader.LOCAL_DATA_DIR)) > 0)

    @staticmethod
    def _process_uploads(uploaded_files) -> List[Document]:
        """Salva uploads em pasta temporária e carrega."""

        if os.path.exists(DocumentLoader.TEMP_DIR):
            shutil.rmtree(DocumentLoader.TEMP_DIR)
        os.makedirs(DocumentLoader.TEMP_DIR, exist_ok=True)

        try:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(DocumentLoader.TEMP_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            # Carrega usando o LlamaIndex
            return SimpleDirectoryReader(DocumentLoader.TEMP_DIR).load_data()
            
        except Exception as e:
            logger.error(f"Erro ao processar uploads: {e}")
            raise e
