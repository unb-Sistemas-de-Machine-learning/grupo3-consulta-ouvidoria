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
        # Spinner só aparece se demorar (ou seja, se for indexar do zero)
        with st.spinner("Verificando base de conhecimento..."):
            try:
                rag_service.ingest_and_index()
                st.session_state.indexed = True
                # st.toast("Base pronta!", icon="✅") # Opcional: Feedback discreto
            except Exception as e:
                st.error(f"Erro ao carregar base: {e}")

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
        with st.expander("Admin: Atualizar Manuais"):
            files = st.file_uploader("Novos Manuais", accept_multiple_files=True)
            if files and st.button("Forçar Reindexação"):
                with st.spinner("Processando novos arquivos..."):
                    rag_service.ingest_and_index(files)
                    st.success("Base atualizada com sucesso!")

    # RENDERIZA CHAT
    if st.session_state.chat_open:
        with col_chat:
            ui.render_chat_interface(rag_service)
            ui.process_new_message(rag_service)

if __name__ == "__main__":
    main()
