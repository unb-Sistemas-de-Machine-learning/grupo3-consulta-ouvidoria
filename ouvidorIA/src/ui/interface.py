import streamlit as st
import json
import re
from config import AppConfig

class OuvidoriaUI:
    def __init__(self):
        self._setup_page()
        self._inject_css()
        self._init_session_state()

    def _setup_page(self):
        st.set_page_config(page_title="Fala.BR - Pedido de Acesso", layout="wide", page_icon="🗣️")

    def _init_session_state(self):
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant", 
                "content": "Olá! Sou o assistente virtual do Fala.BR. Posso ajudar você a preencher este formulário. Me conte o que aconteceu."
            }]
        
        defaults = {
            "form_esfera": "Federal",
            "chat_open": False,
            "pending_suggestion": None,  # Armazena sugestão antes de widgets serem criados
            "apply_suggestion": False    # Flag para aplicar sugestão
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _inject_css(self):
        st.markdown("""
        <style>
            .main { background-color: #ffffff; }
            h1, h2, h3 { font-family: sans-serif; color: #333; }
            .fala-header { display: flex; align-items: center; gap: 15px; margin-bottom: 30px; }
            .fala-icon { background-color: #28a745; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; }
            .fala-title { font-size: 2rem; font-weight: 600; color: #333; margin: 0; }
            .fala-subtitle { color: #666; font-size: 1rem; }
            .form-section-title { font-size: 1.1rem; font-weight: bold; color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-top: 20px; margin-bottom: 15px; }
            .stStatus { background-color: #f8f9fa; border-radius: 10px; padding: 10px; border: 1px solid #ddd; }
        </style>
        """, unsafe_allow_html=True)

    def toggle_chat(self):
        st.session_state.chat_open = not st.session_state.chat_open

    def render_form_header(self):
        st.markdown("""
        <div class="fala-header">
            <div class="fala-icon">i</div>
            <div>
                <div class="fala-title">Faça seu pedido de acesso à informação</div>
                <div class="fala-subtitle">Escolha essa opção para obter informações custodiadas pela Administração Pública.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def render_form_section(self):
        # Verifica se deve aplicar sugestão
        if st.session_state.apply_suggestion and st.session_state.pending_suggestion:
            sug = st.session_state.pending_suggestion
            default_orgao = sug.get("orgao", "")
            default_resumo = sug.get("resumo", "")
            default_conteudo = sug.get("conteudo", "")
            st.session_state.apply_suggestion = False  # Reset flag
            st.success("✅ Formulário preenchido com sugestões do assistente!")
        else:
            default_orgao = ""
            default_resumo = ""
            default_conteudo = ""
        
        st.markdown('<div class="form-section-title">Destinatário</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.selectbox("Esfera", ["Federal", "Estadual", "Municipal"], key="form_esfera")
        
        orgaos = ["", "Ministério da Saúde (MS)", "Ministério da Educação (MEC)", "Controladoria-Geral da União (CGU)", "Instituto Nacional do Seguro Social (INSS)", "Polícia Federal (PF)", "Receita Federal (RFB)"]
        
        # Define índice do órgão
        orgao_index = 0
        if default_orgao in orgaos:
            orgao_index = orgaos.index(default_orgao)
        
        st.selectbox("Órgão destinatário", options=orgaos, index=orgao_index)

        st.markdown('<div class="form-section-title">Descrição</div>', unsafe_allow_html=True)
        st.selectbox("Sobre qual assunto você quer falar?", options=["", "Saúde", "Educação", "Segurança", "Transporte"], key="form_assunto")
        st.text_input("Resumo", placeholder="Digite um breve resumo", value=default_resumo)
        st.text_area("Fale aqui", height=250, placeholder="Descreva o conteúdo do pedido...", value=default_conteudo)

        st.markdown("---")
        c1, c2, c3 = st.columns([1, 4, 1])
        with c3:
            st.button("Avançar →", type="primary", use_container_width=True)

    def render_sidebar(self, rag_service=None):
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Gov.br_logo.svg/1200px-Gov.br_logo.svg.png", width=120)
            st.header("Configurações")
            
            # Status do sistema
            st.info(f"**Status LLM:** Conectado\n\n**Modelo:** {AppConfig.OLLAMA_MODEL}")
            
            # Status do RAG
            if rag_service:
                index_info = rag_service.get_index_info()
                if index_info.get("exists"):
                    st.success("**RAG:** Base de conhecimento ativa")
                else:
                    st.warning("**RAG:** Sem documentos indexados")
            
            st.divider()
            uploaded_files = st.file_uploader("Carregar documentos", accept_multiple_files=True, type=['txt', 'pdf'])
            return uploaded_files

    def render_chat_interface(self, rag_service):
        st.markdown("### 🤖 OuvidorIA")
        chat_container = st.container(height=600)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
                    # SÓ MOSTRA O WIDGET SE NÃO FOR CHAT PURO
                    if "suggestion" in msg:
                        sug = msg["suggestion"]
                        tipo = sug.get("tipo", "CHAT").upper()
                        
                        # Se o tipo for CHAT, não mostramos o widget de preenchimento
                        if sug and tipo != "CHAT":
                            with st.status(f"📝 Sugestão: {tipo}", expanded=True):
                                st.write(f"**Tipo:** {tipo}")
                                st.write(f"**Órgão:** {sug.get('orgao', 'N/A')}")
                                st.write(f"**Resumo:** {tipo} sobre {sug.get('orgao', '')}")
                                
                                st.markdown("**Descrição técnica:**")
                                st.text_area(
                                    "texto_sugestao", 
                                    value=sug.get("resumo_qualificado", ""), 
                                    height=150, 
                                    disabled=True,
                                    label_visibility="collapsed",
                                    key=f"sug_text_{msg.get('id', 0)}"
                                )
                                
                                if st.button("Preencher Formulário", key=f"btn_{msg.get('id', 0)}", type="primary"):
                                    # Armazena sugestão e ativa flag
                                    st.session_state.pending_suggestion = {
                                        "orgao": sug.get("orgao", ""),
                                        "resumo": f"{tipo} sobre {sug.get('orgao', '')}",
                                        "conteudo": sug.get("resumo_qualificado", "")
                                    }
                                    st.session_state.apply_suggestion = True
                                    st.rerun()

        if prompt := st.chat_input("Ex: Não consigo meu remédio no posto..."):
            st.session_state.messages.append({"role": "user", "content": prompt, "id": len(st.session_state.messages)})
            st.rerun()

    def process_new_message(self, rag_service):
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            last_msg = st.session_state.messages[-1]["content"]
            with st.spinner("OuvidorIA pensando..."):
                try:
                    raw_response = rag_service.analyze_demand(last_msg)
                    
                    if not raw_response or len(raw_response.strip()) == 0:
                        st.error("Resposta vazia do modelo. Tente novamente.")
                        return
                    
                    # Limpa markdown code blocks se houver
                    clean_response = re.sub(r'```json\s*|\s*```', '', raw_response).strip()
                    
                    # Tenta extrair JSON
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', clean_response, re.DOTALL)
                    suggestion = {}
                    text_response = "Desculpe, não consegui processar sua mensagem. Tente novamente."
                    
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            suggestion = json.loads(json_str)
                            
                            # Se for CHAT, usamos a resposta_chat do JSON como texto principal
                            if suggestion.get("tipo", "").upper() == "CHAT":
                                text_response = suggestion.get("resposta_chat", "Olá! Como posso ajudar?")
                            else:
                                # Se for RELATO, criamos um texto de introdução para o widget
                                text_response = suggestion.get("resposta_chat", "Analisei seu caso. Veja a sugestão de preenchimento abaixo:")
                        except json.JSONDecodeError as je:
                            st.error(f"Erro ao parsear JSON: {je}")
                            st.error(f"JSON recebido: {json_str[:200]}")
                            text_response = "Erro ao processar resposta. Tente reformular sua mensagem."
                    else:
                        st.warning("Nenhum JSON encontrado na resposta")
                        st.text(f"Resposta recebida: {clean_response[:300]}")
                        text_response = "Não consegui processar sua mensagem no formato esperado. Tente novamente."
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": text_response, 
                        "suggestion": suggestion,
                        "id": len(st.session_state.messages)
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar resposta: {e}")
                    import traceback
                    st.error(traceback.format_exc())
