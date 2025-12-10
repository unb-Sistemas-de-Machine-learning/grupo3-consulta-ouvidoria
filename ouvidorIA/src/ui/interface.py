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
            "chat_open": True,  # Chat inicia aberto
            "pending_suggestion": None,  # Armazena sugestão antes de widgets serem criados
            "apply_suggestion": False,   # Flag para aplicar sugestão
            "processing_message": False  # Flag para evitar processamento duplicado
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
    
    def _map_organ_to_subject(self, orgao: str) -> str:
        """Mapeia órgão para assunto correspondente."""
        orgao_lower = orgao.lower()
        
        if "saúde" in orgao_lower or "saude" in orgao_lower:
            return "Saúde"
        elif "educação" in orgao_lower or "educacao" in orgao_lower:
            return "Educação"
        elif "polícia" in orgao_lower or "policia" in orgao_lower or "segurança" in orgao_lower:
            return "Segurança"
        else:
            return ""

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
            default_esfera = sug.get("esfera", "Federal")
            default_orgao = sug.get("orgao", "")
            default_assunto = sug.get("assunto", "")
            default_resumo = sug.get("resumo", "")
            default_conteudo = sug.get("conteudo", "")
            st.session_state.apply_suggestion = False  # Reset flag
            st.success("✅ Formulário preenchido com sugestões do assistente!")
        else:
            default_esfera = "Federal"
            default_orgao = ""
            default_assunto = ""
            default_resumo = ""
            default_conteudo = ""
        
        st.markdown('<div class="form-section-title">Destinatário</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            esferas = ["Federal", "Estadual", "Municipal"]
            esfera_index = esferas.index(default_esfera) if default_esfera in esferas else 0
            st.selectbox("Esfera", esferas, index=esfera_index)
        
        orgaos = ["", "Ministério da Saúde (MS)", "Ministério da Educação (MEC)", "Controladoria-Geral da União (CGU)", "Instituto Nacional do Seguro Social (INSS)", "Polícia Federal (PF)", "Receita Federal (RFB)"]
        
        # Define índice do órgão (busca exata ou parcial)
        orgao_index = 0
        if default_orgao:
            # Tenta match exato primeiro
            if default_orgao in orgaos:
                orgao_index = orgaos.index(default_orgao)
            else:
                # Busca parcial (case insensitive)
                default_lower = default_orgao.lower()
                for i, orgao in enumerate(orgaos):
                    if orgao and (default_lower in orgao.lower() or orgao.lower() in default_lower):
                        orgao_index = i
                        break
        
        st.selectbox("Órgão destinatário", options=orgaos, index=orgao_index)

        st.markdown('<div class="form-section-title">Descrição</div>', unsafe_allow_html=True)
        
        assuntos = ["", "Saúde", "Educação", "Segurança", "Transporte"]
        assunto_index = 0
        if default_assunto and default_assunto in assuntos:
            assunto_index = assuntos.index(default_assunto)
        
        st.selectbox("Sobre qual assunto você quer falar?", options=assuntos, index=assunto_index)
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
                            # Determina assunto e esfera baseado no órgão
                            orgao = sug.get("orgao", "")
                            assunto = self._map_organ_to_subject(orgao)
                            esfera = "Federal"  # Todos os órgãos listados são federais
                            
                            with st.status(f"📝 Sugestão: {tipo}", expanded=True):
                                st.write(f"**Tipo:** {tipo}")
                                st.write(f"**Esfera:** {esfera}")
                                st.write(f"**Órgão:** {orgao if orgao else 'N/A'}")
                                st.write(f"**Assunto:** {assunto if assunto else 'N/A'}")
                                st.write(f"**Resumo:** {sug.get('resumo', tipo + ' - ' + orgao)}")
                                
                                st.markdown("**Fundamentação:**")
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
                                        "esfera": esfera,
                                        "orgao": orgao,
                                        "assunto": assunto,
                                        "resumo": sug.get("resumo", f"{tipo} - {orgao}"),
                                        "conteudo": sug.get("resumo_qualificado", "")
                                    }
                                    st.session_state.apply_suggestion = True
                                    st.session_state.processing_message = False  # Reset flag
                                    st.rerun()

        if prompt := st.chat_input("Ex: Não consigo meu remédio no posto..."):
            st.session_state.messages.append({"role": "user", "content": prompt, "id": len(st.session_state.messages)})
            st.session_state.processing_message = True
            st.rerun()

    def process_new_message(self, rag_service):
        # Só processa se a flag estiver ativa e última mensagem for do usuário
        if not st.session_state.get("processing_message", False):
            return
        
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.processing_message = False  # Desativa a flag imediatamente
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
