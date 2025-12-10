import streamlit as st
import logging

from src.ui.interface import OuvidoriaUI
from src.rag.service import OuvidoriaRAGService

logging.basicConfig(level=logging.INFO)

@st.cache_resource(show_spinner=False)
def get_service():
    return OuvidoriaRAGService()

def main():
    ui = OuvidoriaUI()
    rag_service = get_service()

    # --- HEADER / BLOB ---
    top_col1, top_col2 = st.columns([6, 1])
    with top_col1:
        st.title("📢 Portal da Ouvidoria")
    with top_col2:
        if st.button("💬 Ajuda", type="primary", help="Abrir Assistente Inteligente"):
            ui.toggle_chat()

    # --- INDEXAÇÃO AUTOMÁTICA (Persistente) ---
    if "indexed" not in st.session_state:
        from config import AppConfig
        
        rebuild_msg = "Reconstruindo índice do zero..." if AppConfig.FORCE_REBUILD_INDEX else "Carregando base de conhecimento da ouvidoria..."
        with st.spinner(rebuild_msg):
            try:
                rag_service.ingest_and_index(force_rebuild=AppConfig.FORCE_REBUILD_INDEX)
                st.session_state.indexed = True
                
                # Mostra informação sobre o índice carregado
                index_info = rag_service.get_index_info()
                if index_info.get("exists"):
                    rebuild_note = " (reconstruído)" if AppConfig.FORCE_REBUILD_INDEX else ""
                    st.success(f"Base de conhecimento carregada{rebuild_note}. Documentos indexados.")
                else:
                    st.warning("Índice vazio. Adicione documentos na pasta data/raw/")
            except Exception as e:
                st.error(f"Erro ao carregar base: {e}")
                st.error("Verifique se existem arquivos PDF na pasta data/raw/")

    # --- LAYOUT PRINCIPAL ---
    if st.session_state.chat_open:
        col_form, col_chat = st.columns([1.5, 1])
    else:
        col_form, col_chat = st.columns([1, 0.01])

    # RENDERIZA FORMULÁRIO
    with col_form:
        ui.render_form_header() # Adicionado Header do Fala.BR
        ui.render_form_section()
        
        # Área administrativa para forçar atualização
        with st.expander("Admin: Gerenciar Base de Conhecimento"):
            st.subheader("Reindexar documentos existentes")
            if st.button("Reconstruir Índice", help="Reprocessa todos os PDFs em data/raw/"):
                with st.spinner("Reconstruindo índice..."):
                    rag_service.ingest_and_index(force_rebuild=True)
                    st.success("Índice reconstruído com sucesso!")
                    st.session_state.indexed = False
                    st.rerun()
            
            st.divider()
            st.subheader("Adicionar novos documentos")
            files = st.file_uploader("Novos Manuais", accept_multiple_files=True, type=['pdf', 'txt'])
            if files and st.button("Indexar Novos Arquivos"):
                with st.spinner("Processando novos arquivos..."):
                    rag_service.ingest_and_index(files, force_rebuild=True)
                    st.success("Novos documentos indexados com sucesso!")
                    st.session_state.indexed = False
                    st.rerun()

    # RENDERIZA CHAT
    if st.session_state.chat_open:
        with col_chat:
            ui.render_chat_interface(rag_service)
            ui.process_new_message(rag_service)

if __name__ == "__main__":
    main()
