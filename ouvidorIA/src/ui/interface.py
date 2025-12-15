import streamlit as st
import json
import re
import logging
from typing import Dict, Any, List
from config import AppConfig

logger = logging.getLogger(__name__)

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
        
        orgaos = ["", "ABGF - Agencia Brasileira Gestora de Fundos Garantidores e Garantias S.A.", "ABIN – Agência Brasileira de Inteligência", "AEB – Agência Espacial Brasileira", "Agência Brasil;Rádio Nacional do Alto Solimões;Rádio Nacional AM do RJ;Rádio Nacional da Amazônia;Radioagência Nacional;Rádio Nacional FM;Rádio Nacional AM de Brasília;Rádio Nacional FM;Rádios MEC;TV Brasil;EBC Play;EBC - Gestão;EBC - Empresa Brasil de Comunicação S. A.;Portal EBC;Rádios EBC-Aplicativo [EBC – Empresa Brasil de Comunicação S.A.]", "AGU – Advocacia-Geral da União", "AMAZUL - Amazônia Azul Tecnologias de Defesa S.A.", "ANA – Agência Nacional de Águas", "ANAC – Agência Nacional de Aviação Civil", "ANATEL – Agência Nacional de Telecomunicações", "ANCINE – Agência Nacional do Cinema", "ANEEL – Agência Nacional de Energia Elétrica", "ANP – Agência Nacional do Petróleo, Gás Natural e Biocombustíveis", "ANPD - Autoridade Nacional de Proteção de Dados", "ANS – Agência Nacional de Saúde Suplementar", "ANTAQ – Agência Nacional de Transportes Aquaviários", "ANTT – Agência Nacional de Transportes Terrestres", "ANVISA – Agência Nacional de Vigilância Sanitária", "Arquivo Nacional [MGI - Ministério da Gestão e da Inovação em Serviços Públicos]", "Autoridade Portuária de Santos S.A.", "BACEN – Banco Central do Brasil", "BASA – Banco da Amazônia S.A.", "BB – Banco do Brasil S.A.", "BBTS [BB Tecnologia e Serviços]", "BBTur Viagens e Turismo Ltda", "BNB – Banco do Nordeste do Brasil S.A.", "BNDES – Banco Nacional de Desenvolvimento Econômico e Social", "CADE – Conselho Administrativo de Defesa Econômica", "CAPES – Coordenação de Aperfeiçoamento de Pessoal de Nível Superior", "CBPF - Centro Brasileiro de Pesquisas Físicas [Ministério da Ciência, Tecnologia e Inovação] [CBPF – Centro Brasileiro de Pesquisas Físicas]", "CBTU – Companhia Brasileira de Trens Urbanos", "CBTU - Superintendência de Trens Urbanos de João Pessoa", "CBTU - Superintendência de Trens Urbanos de Natal", "CBTU - Superintendência de Trens Urbanos de Recife", "CDC – Companhia Docas do Ceará", "CDP – Companhia Docas do Pará", "CDRJ – Companhia Docas do Rio de Janeiro", "CEAGESP – Companhia de Entrepostos e Armazéns Gerais de São Paulo", "CEASA-MG – Centrais de Abastecimento de Minas Gerais S.A.", "CEF – Caixa Econômica Federal", "CEFET-MG – Centro Federal de Educação Tecnológica de Minas Gerais", "CEFET-RJ – Centro Federal de Educação Tecnológica Celso Suckow da Fonseca", "CEITEC/S.A. – Centro Nacional de Tecnologia Eletrônica Avançada S.A.", "CEMADEN - Centro Nacional de Monitoramento e Alertas de Desastres Naturais [Ministério da Ciência, Tecnologia e Inovação] [CEMADEN-Centro Nacional de Monitoramento e Alertas de Desastres Naturais]", "CEP - Comissão de Ética Pública/PR [PR – Presidência da República]", "CETEM - Centro de Tecnologia Mineral [Ministério da Ciência, Tecnologia e Inovação] [CETEM – Centro de Tecnologia Mineral]", "CETENE - Centro de Tecnologias Estratégicas do Nordeste [Ministério da Ciência, Tecnologia e Inovação] [CETENE – Centro de Tecnologias Estratégicas do Nordeste]", "CEX – Comando do Exército", "CFIAE – Caixa de Financiamento Imobiliário da Aeronáutica", "CGU – Controladoria-Geral da União", "CGU/SNAI - Secretaria Nacional de Acesso à Informação", "CMAR – Comando da Marinha", "CMB – Casa da Moeda do Brasil", "CMRI - Comissão Mista de Reavaliação de Informações", "CNEN – Comissão Nacional de Energia Nuclear", "CNPQ – Conselho Nacional de Desenvolvimento Científico e Tecnológico", "COAF - Conselho de Controle de Atividades Financeiras", "CODEBA – Companhia das Docas do Estado da Bahia", "CODERN – Companhia Docas do Rio Grande do Norte", "CODEVASF – Companhia de Desenvolvimento dos Vales do São Francisco e do Parnaíba", "COMAER – Comando da Aeronáutica", "CONAB – Companhia Nacional de Abastecimento", "Conselho Federal de Contabilidade", "Conselho Federal de Corretores de Imóveis - COFECI/DF", "CP II – Colégio Pedro II", "CPRM – Companhia de Pesquisa de Recursos Minerais", "CTI - Centro de Tecnologia da Informação Renato Archer [Ministério da Ciência, Tecnologia e Inovação] [CTI – Centro de Tecnologia da Informação Renato Archer]", "CVM – Comissão de Valores Mobiliários", "DATAPREV – Empresa de Tecnologia e Informações da Previdência", "DEPEN – Departamento Penitenciário Nacional [Senappen - Secretaria Nacional de Políticas Penais]", "DNIT – Departamento Nacional de Infraestrutura de Transportes", "DNOCS – Departamento Nacional de Obras Contra as Secas", "DNPM;Departamento Nacional de Produção Mineral [ANM - Agência Nacional de Mineração]", "EBSERH – CHC-UFPR (HC e MVFA) Complexo do Hospital de Clínicas da Universidade Federal do Paraná", "EBSERH - CH-UFC - Complexo Hospitalar da Universidade Federal do Ceará - Hospital Universitário Walter Cantídio (HUWC) e Maternidade Escola Assis Chateaubriand (MEAC)", "EBSERH – CHU-UFPA (HUJBB e HUBFS) – Complexo Hospitalar Universitário da Universidade Federal do Pará – Hospitais Universitários João de Barros Barreto e Bettina Ferro de Souza", "EBSERH - Filial Complexo Hospitalar da UFRJ (HUCFF, IPPMG, ME)", "EBSERH - HC-UFG - Hospital das Clínicas da Universidade Federal de Goiás", "EBSERH - HC-UFMG - Hospital das Clínicas da Universidade Federal de Minas Gerais", "EBSERH - HC-UFPE - Hospital das Clínicas de Pernambuco", "EBSERH - HC-UFTM - Hospital das Clínicas da Universidade Federal do Triângulo Mineiro", "EBSERH - HC-UFU - Hospital de Clínicas de Uberlândia", "EBSERH - HDT/UFT - Hospital de Doenças Tropicais", "EBSERH - HE-UFPEL - Hospital Escola da Universidade Federal de Pelotas", "EBSERH - HUAB-UFRN - Hospital Universitário Ana Bezerra", "EBSERH - HUAC-UFCG - Hospital Universitário Alcides Carneiro", "EBSERH - HUAP-UFF - Hospital Universitário Antônio Pedro", "EBSERH - HUB-UNB - Hospital Universitário de Brasília", "EBSERH - HUCAM-UFES - Hospital Universitário Cassiano Antônio Moraes", "EBSERH - HU-FURG - Hospital Universitário Dr. Miguel Riet Côrrea Júnior", "EBSERH - HUGG - UNIRIO - Hospital Universitário Gaffrée e Guinle", "EBSERH - HUGV-UFAM – Hospital Universitário Getúlio Vargas", "EBSERH - HUJB-UFCG - Hospital Universitário Júlio Maria Bandeira de Mello", "EBSERH - HUJM-UFMT – Hospital Universitário Julio Muller", "EBSERH - HUL-UFS - Hospital Regional de Lagarto", "EBSERH - HULW-UFPB - Hospital Universitário Lauro Wanderley", "EBSERH - HUMAP-UFMS - Hospital Universitário Maria Aparecida Pedrossian", "EBSERH - HUOL-UFRN - Hospital Universitário Onofre Lopes", "EBSERH - HUPAA-UFAL - Hospital Universitário Professor Alberto Antunes", "EBSERH - HUSM-UFSM - Hospital Universitário de Santa Maria", "EBSERH - HU-UFGD – Hospital Universitário de Grande Dourados", "EBSERH - HU-UFJF - Hospital Universitário de Juiz de Fora", "EBSERH - HU-UFMA - Hospital Universitário da Universidade Federal do Maranhão", "EBSERH - HU-UFPI - Hospital Universitário da Universidade Federal do Piauí", "EBSERH - HU-UFS - Hospital Universitário da Universidade Federal de Sergipe", "EBSERH - HU-UFSC - Hospital Universitário Professor Polydoro Ernani de São Thiago", "EBSERH - HU-UFSCAR - Hospital Universitário da Universidade Federal de São Carlos", "EBSERH - HU-UNIVASF - Hospital de Ensino Dr. Washington Antônio de Barros", "EBSERH - MCO-UFBA - Maternidade Climério de Oliveira", "EBSERH - MEJC-UFRN - Maternidade Escola Januário Cicco", "EBSERH – sede - Empresa Brasileira de Serviços Hospitalares", "EBSERH- HU-UNIFAP- Hospital Universitário da Universidade Federal do Amapá", "EBSERH/HUPES-UFBA – EBSERH - Filial Hospital Universitário Edgard Santos", "ECT – Empresa Brasileira de Correios e Telégrafos", "ELETRONUCLEAR S.A.", "EMBRAPA – Empresa Brasileira de Pesquisa Agropecuária", "EMGEA – Empresa Gestora de Ativos", "EMGEPRON – Empresa Gerencial de Projetos Navais", "ENBpar - Empresa Brasileira de Participações em Energia Nuclear e Binacional S.A", "EPE – Empresa de Pesquisa Energética", "ESAF - Escola de Administração Fazendária [ENAP – Fundação Escola Nacional de Administração Pública]", "ESD - Escola Superior de Defesa", "ESG – Escola Superior de Guerra", "FBN – Fundação Biblioteca Nacional", "FCO - Fundo Constitucional de Financiamento do Centro-Oeste", "FCP – Fundação Cultural Palmares", "FCRB – Fundação Casa de Rui Barbosa", "FINEP – Financiadora de Estudos e Projetos", "FIOCRUZ – Fundação Oswaldo Cruz", "FNDE – Fundo Nacional de Desenvolvimento da Educação", "FNE - Fundo Constitucional de Financiamento do Nordeste", "FNO - Fundo Constitucional de Financiamento do Norte", "FUNAG – Fundação Alexandre de Gusmão", "FUNAI – Fundação Nacional dos Povos Indígenas", "FUNARTE – Fundação Nacional de Artes", "FUNASA – Fundação Nacional de Saúde", "FUNDACENTRO – Fundação Jorge Duprat Figueiredo, de Segurança e Medicina do Trabalho", "FUNDAJ – Fundação Joaquim Nabuco", "FUNPRESP - Fundação de Previdência Complementar do Servidor Público Federal do Poder Executivo", "FUNRei - Fundação Universidade Federal de São João Del Rei", "FURG – Fundação Universidade Federal do Rio Grande", "GSI-PR – Gabinete de Segurança Institucional da Presidência da República", "HCPA – Hospital de Clínicas de Porto Alegre", "HEMOBRÁS – Empresa Brasileira de Hemoderivados e Biotecnologia", "HFA – Hospital das Forças Armadas", "HNSC – Hospital Nossa Senhora da Conceição S.A.", "Hospital Cristo Redentor S/A", "Hospital Federal Cardoso Fontes", "Hospital Federal da Lagoa", "Hospital Federal de Bonsucesso", "Hospital Federal de Ipanema", "Hospital Federal do Andaraí", "Hospital Federal dos Servidores do Estado (RJ)"]
        
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
        
        assuntos = ["", "Abastecimento e armazenagem", "Acesso à terra", "Ações Afirmativas", "Acordo Rio Doce", "Aeronáutica", "Agricultura Familiar", "Água", "Apoio ao empreendedorismo, empresas, ME, EPP e MEI", "Assédio moral", "Assédio sexual", "Assistência Estudantil", "Assistência Hospitalar e Ambulatorial", "Atendimento ao público", "Autorização, Regulação e Fiscalização", "Benefícios e serviços", "Bibliotecas e Acervos Públicos", "Biodiversidade", "Cadastros e Documentação", "Calamidades/Desastres", "Canais de atendimento", "Certidões e Declarações", "Ciência, tecnologia e inovação", "Cinema e audiovisual", "Clima", "Combate a endemias e epidemias", "Comércio Exterior", "Compras públicas", "Concursos e processos seletivos", "Condições Rodovia", "Conduta ética e irregularidades de servidores", "Conta Gov.Br", "Controle Social", "Cooperativismo e associativismo", "COP30", "Correios", "Corrupção", "Crimes Ambientais", "Cuidado e Acolhimento", "Cultura", "Dados Pessoais - LGPD", "Defesa Civil", "Defesa da concorrência e do consumidor; defesa comercial", "Defesa e vigilância sanitária", "Defesa Nacional", "Denúncia Crime", "Descontos e Consignações", "Desenvolvimento da indústria, do comércio e dos serviços", "Direitos autorais", "Documentação e Serviço Militar", "Economia e Finanças", "Educação ambiental", "Educação Básica", "Educação Profissional e Tecnológica", "Educação Superior", "Emendas Parlamentares", "Energia", "Esporte", "Estudos e Pesquisas", "Exército", "Extrativismo", "Fiscalização do Estado", "Frete", "Fundos", "Gestão de Pessoas", "Gestão escolar e administrativa", "Gestão Pública", "Guia Lilás - Orientações para prevenção e tratamento ao assédio moral e sexual e à discriminação no Governo Federal", "Impostos, Dívida Ativa e Receita Federal", "Inclusão Digital", "Informações processuais", "Infraestrutura rural e urbana", "Irrigação e infraestrutura hídrica", "Lavagem de dinheiro", "Marinha", "Medicamentos, aparelhos e produtos em saúde", "Meio ambiente", "Meteorologia", "Metrologia, normalização e qualidade industrial", "Mineração", "Minha Casa, Minha Vida e outras ações de habitação", "Museus e galerias", "Normas e Fiscalização", "Operações CGU", "Para o Empresário e Empreendedor", "Patrimônio histórico, artístico e cultural", "Patrimônio Público", "Patrocínio", "Pesagem", "Pesca Amadora e Esportiva", "Pesca e Aquicultura", "Pesquisa e Desenvolvimento", "Pesquisa, inovação e assistência técnica", "Petróleo, Gás e Biocombustíveis", "Planos de saúde", "Política agrícola", "Ponto de Parada e Descanso - PPD", "Prêmios e Apostas", "Produção Agropecuária", "Produtos e Atividades Controladas", "Programa Nacional de Capacitação das Cidades", "Programas e Benefícios Sociais", "propriedade industrial, intelectual e transferência de tecnologia", "Proteção ambiental", "Proteção e Benefícios ao Trabalhador", "Publicidade", "Quilombolas, povos originários e comunidades tradicionais de matriz africana, ciganos e outras minorias", "Racismo e Discriminação", "Rede de Assistência e Proteção Social", "Redes Sociais", "Regime de Previdência Próprio e Complementar", "Regime de trabalho", "Registro e Cadastro de Empresas", "Regularização Fundiária Urbana", "Rejeitos e resíduos", "Relações internacionais", "Saneamento ambiental", "Saúde Animal e Sanidade vegetal", "Segurança Alimentar e Nutricional", "Serviços para Estrangeiros", "Sistema Penitenciário", "Taxas e cadastros", "Tecnologia da Informação e Sistemas", "Telecomunicações", "Transformação digital e desenvolvimento da automação", "Trânsito e mobilidade", "Transparência e acesso à informação", "Transporte Aéreo", "Transporte aquaviário", "Transporte Ferroviário", "Transporte passageiros e cargas", "Transporte Rodoviário", "Turismo", "TV Radiodifusão e outras mídias", "Vacinação", "Vigilância em Saúde"]
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

    def render_sidebar(self, api_client=None):
        with st.sidebar:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Gov.br_logo.svg/1200px-Gov.br_logo.svg.png", width=120)
            st.header("Configurações")
            
            # Status do sistema
            st.info(f"**Status LLM:** Conectado\n\n**Modelo:** {AppConfig.OLLAMA_MODEL}")
            
            # Status do RAG
            if api_client:
                try:
                    index_info = api_client.get_index_info()
                    if index_info.get("exists"):
                        st.success("**RAG:** Base de conhecimento ativa")
                    else:
                        st.warning("**RAG:** Sem documentos indexados")
                except Exception as e:
                    st.error(f"**RAG:** Erro ao conectar com API: {e}")
            
            st.divider()
            uploaded_files = st.file_uploader("Carregar documentos", accept_multiple_files=True, type=['txt', 'pdf'])
            return uploaded_files

    def render_chat_interface(self, api_client):
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
                                    key=f"sug_text_{len(st.session_state.messages)}"
                                )
                                
                                if st.button("Preencher Formulário", key=f"btn_{len(st.session_state.messages)}", type="primary"):
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
            st.session_state.messages.append({
                "role": "user", 
                "content": prompt
            })
            st.session_state.processing_message = True
            st.rerun()

    def process_new_message(self, api_client):
        """Process new user messages synchronously."""
        # Find the last user message that doesn't have a response yet
        messages = st.session_state.messages
        if not messages:
            return
        
        # Check if the last message is from user and doesn't have a response
        last_msg = messages[-1]
        if last_msg["role"] == "user" and st.session_state.processing_message:
            user_text = last_msg["content"]
            logger.info(f"Processing user message: {user_text[:50]}...")
            
            try:
                # Show spinner while processing
                with st.spinner("OuvidorIA está pensando..."):
                    # Make synchronous API call
                    result = api_client.analyze_demand(user_text)
                
                # Extract data from API response
                suggestion = {
                    "tipo": result.get("tipo", ""),
                    "orgao": result.get("orgao"),
                    "resumo": result.get("resumo"),
                    "resumo_qualificado": result.get("resumo_qualificado"),
                    "resposta_chat": result.get("resposta_chat", "")
                }
                
                # Se for CHAT, usamos a resposta_chat como texto principal
                if suggestion.get("tipo", "").upper() == "CHAT":
                    text_response = suggestion.get("resposta_chat", "Olá! Como posso ajudar?")
                else:
                    # Se for RELATO, criamos um texto de introdução para o widget
                    text_response = suggestion.get("resposta_chat", "Analisei seu caso. Veja a sugestão de preenchimento abaixo:")
                
                # Add assistant response
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": text_response, 
                    "suggestion": suggestion
                })
                
                st.session_state.processing_message = False
                logger.info("Message processed successfully")
                st.rerun()
                
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                st.error(f"Erro ao processar mensagem: {e}")
                st.session_state.processing_message = False
                # Add error message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
                })
                st.rerun()
