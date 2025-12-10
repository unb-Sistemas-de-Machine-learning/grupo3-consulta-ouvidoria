# Arquitetura da Solução

## Diagrama Arquitetural do MVP

![Diagrama de arquitetura do MVP](../images/arquitetura-mvp.png)


**Legenda**

* **🧱 (Blocos de Código):** Serviços, componentes de software, processos.
* **🗂️ (Arquivos/Dados):** Fontes de dados estáticas ou artefatos gerados.
* **🗄️ (Banco de Dados):** Soluções de armazenamento persistente.
* **☁️ (Serviço Externo):** APIs de terceiros.
* **👤 (Ator):** Usuário humano do sistema.

---

### Camada FRONTEND (React)

A camada de interação direta com o `👤 Cidadão`. É responsável por toda a experiência do usuário.

* **Interface Web:** Ponto de entrada principal. Renderiza um formulário que simula a página de envio de manifestações (inspirado no [fala.BR](https://falabr.cgu.gov.br/web/home)) e serve como contêiner para o componente de chat.
* **Chatbot:** Componente integrado à `Interface Web`. Utiliza comunicação via **WebSocket** para interações de baixa latência com o backend, proporcionando uma experiência de conversa fluida e em tempo real.

### Camada BACKEND (Python)

O núcleo do sistema, responsável pela lógica de negócios, processamento de ML e gerenciamento de dados. É composto por serviços que se comunicam internamente.

* **API Gateway (RestAPI):** Ponto de entrada único do backend (Single Point of Entry). Construído em **FastAPI**, gerencia todas as requisições HTTP (da `Interface Web`) e as conexões WebSocket (do `Chatbot`), roteando-as para os serviços internos apropriados, primariamente o `Orquestrador`.

* **Orquestrador:** O "cérebro" da aplicação. Recebe as chamadas da API Gateway e executa a lógica de negócios da conversa:
    1.  Chama o `Serviço Interpretador` para extrair a intenção e entidades da mensagem do usuário.
    2.  Com base na intenção, decide qual serviço acionar (neste MVP, o `Serviço RAG`).
    3.  Chama o `Repositório` (de forma assíncrona) para salvar o log da interação (pergunta do usuário e resposta do bot).

* **Serviço Interpretador:** Faz o carregamento do NLU (Natural Language Understanding). Sua responsabilidade é carregar os `🗂️ Artefatos BERT` (gerados pela pipeline `ML_NLU`) e expor um endpoint que recebe um texto e retorna um JSON estruturado com a *intenção* e as *entidades* extraídas.

* **Serviço RAG:** Responsável pela Geração Aumentada por Recuperação (RAG). Utiliza o **LlamaIndex** para:
    1.  Receber a consulta (e o histórico de chat) do `Orquestrador`.
    2.  Buscar por contexto relevante no `🗄️ Banco Vetorial (Qdrant)`.
    3.  Construir o prompt final (consulta + contexto + regras de prompt) e enviá-lo para a `☁️ LLM (Gemini API)`.
    4.  Gerenciar a memória da conversa por sessão de usuário.

* **Repositório (Repo):** Camada de abstração de dados (Data Access Layer). Utiliza o **SQLAlchemy** como ORM para gerenciar as operações de CRUD com o `🗄️ Banco Relacional (PostgreSQL)`, tratando exclusivamente do salvamento dos logs da conversa.

### Camada de PIPELINES DE TREINAMENTO (Offline)

Processos executados em lote ("offline") que criam os artefatos de ML e os dados necessários para o funcionamento dos serviços de backend.

* **Scrapers:** Scripts (usando BeautifulSoup) que varrem os `🗂️ Sites Governamentais (URL)` em busca de manuais, leis e documentos públicos.
* **Ingestão RAG:** Pipeline do **LlamaIndex** que recebe os `🗂️ Documentos (PDF)` e os dados processados pelos `Scrapers`. Ele é responsável por dividir (chunking), vetorizar (embedding) e inserir esse conhecimento no `🗄️ Banco Vetorial (Qdrant)`.
* **ML_NLU:** Pipeline de treinamento (fine-tuning) do **BERTimbau** para as tarefas de extração de intenção e entidades. Ela é alimentada pela `☁️ LLM (Gemini API)` num modelo "Zero Treinamento" com prompt para definição de intenções e entidades e gera os `🗂️ Artefatos BERT` como sua saída.

### Banco de Dados e Serviços Externos

Componentes de armazenamento e APIs de terceiros que suportam a arquitetura.

* **Banco Vetorial (Qdrant):** Por meio da pipeline `Ingestão RAG` Armazena o **conhecimento** da organização (documentos, manuais, heurísticas) em formato de vetores. É lido pelo `Serviço RAG` para realizar buscas semânticas rápidas.
* **Banco Relacional (PostgreSQL):** Armazena os **logs** de todas as interações do chat. É escrito pelo `Repositório` e serve como fonte de dados para auditoria, debugging e futuros treinamentos (como Topic Modeling).
* **LLM (Gemini API):** Serviço externo ☁️ (Google) que atua como o cérebro de geração de linguagem. É chamado pelo `Serviço RAG` para formular as respostas finais ao usuário e também pelo `ML NLU` para geração das entradas de treinamento do modelo.

## [Esboço] Diagrama Arquitetural Completo


![Diagrama de arquitetura do projeto completo](../images/arquitetura-completa.png)
