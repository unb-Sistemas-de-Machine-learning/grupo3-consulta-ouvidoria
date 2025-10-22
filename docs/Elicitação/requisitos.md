# Requisitos

A seção de requisitos estabelece as bases formais para o desenvolvimento do OuvidorIA.

Requisitos de software são descrições das funcionalidades, capacidades e restrições de um sistema. Eles são divididos em **Requisitos Funcionais** (RF), que definem o que o sistema deve fazer, e **Requisitos Não Funcionais** (RNF), que definem como o sistema deve operar em termos de qualidade e restrição. 

Para este projeto, adotamos uma **separação entre Requisitos de Produto**, focados na experiência do usuário, **e Requisitos de Machine Learning**, que detalham as capacidades técnicas dos modelos de IA subjacentes.

## 1. Requisitos de Produto

### 1.1. Requisitos Funcionais de Produto (RF-PROD)

| **Código do req.** | **Nome** | **Descrição** |
|-|-|-|
| RF-PROD-001 | Interação por Chat | O produto deve fornecer uma interface de chat para que o usuário possa interagir com o assistente virtual em linguagem natural. |
| RF-PROD-002 | Consulta de Informações sobre Ouvidoria | O usuário deve poder fazer perguntas abertas sobre leis, manuais e procedimentos, e receber respostas textuais claras e objetivas na interface do chat. |
| RF-PROD-003 | Exibição de Fontes da Informação | O produto deve exibir a origem das informações fornecidas (ex: nome da lei, seção do manual), quando aplicável, para aumentar a confiança do usuário. |
| RF-PROD-004 | Assistência no Preenchimento de Formulário | O produto deve, a partir de um texto do usuário, apresentar sugestões para os campos de um formulário de manifestação (ex: Tipo, Órgão). |
| RF-PROD-005 | Edição de Campos Sugeridos | O usuário deve ter o controle final sobre os campos sugeridos, podendo aceitá-los, modificá-los ou preenchê-los manualmente. |
| RF-PROD-006 | Análise de Qualidade de Texto sob Demanda | O usuário deve poder solicitar uma análise do texto de sua manifestação e visualizar um score de qualidade retornado pelo sistema. |
| RF-PROD-007 | Apresentação de Sugestões de Escrita | Com base na análise de qualidade, o produto deve apresentar ao usuário sugestões claras e práticas para melhorar seu texto. |
| RF-PROD-008 | Controle sobre Alterações no Texto | O usuário deve poder visualizar, aceitar ou rejeitar as sugestões de alteração no texto, mantendo sempre o controle sobre a versão final de sua manifestação. |
| RF-PROD-009 | Dashboard de Análise para Gestores | O produto deve fornecer um dashboard com acesso restrito que exiba visualmente os principais temas e tópicos identificados nas conversas dos usuários. |

### 1.2. Requisitos Não Funcionais de Produto (RNF-PROD)

| **Código do req.** | **Nome** | **Descrição** |
|-|-|-|
| RNF-PROD-001 | Usabilidade da Interface | A interface do chatbot e do dashboard deve ser intuitiva e acessível. |
| RNF-PROD-002 | Desempenho da Interação | O tempo de resposta para qualquer interação do usuário com o chatbot não deve exceder 5 segundos (P95). |
| RNF-PROD-003 | Disponibilidade do Serviço | O serviço deve estar disponível para os usuários 99.5% do tempo durante o horário comercial. |
| RNF-PROD-004 | Conformidade Legal (LGPD) | O produto deve estar em total conformidade com a Lei Geral de Proteção de Dados, garantindo a privacidade e a segurança das informações dos usuários. |

# 2. Requisitos de Machine Learning

### 2.1. Requisitos Funcionais de ML (RF-ML)

| **Código do req.** | **Nome** | **Descrição** |
|-|-|-|
| RF-ML-001 | Recuperação de Informação em Base de Documentos (RAG) | O sistema de ML deve ser capaz de, a partir de uma consulta em linguagem natural, buscar e recuperar os trechos de texto mais relevantes de uma base de documentos legais e manuais previamente indexada.
| RF-ML-002 | Geração de Texto em Linguagem Simples (LLM) | O modelo de linguagem (LLM) deve ser capaz de sintetizar as informações recuperadas pelo RAG e gerar respostas coesas, precisas e em linguagem acessível ao cidadão comum.
| RF-ML-003 | Extração de Entidades e Intenções | O modelo de NLP deve ser capaz de processar o texto inicial do usuário para extrair intenções primárias (ex: fazer denúncia) e entidades relevantes (ex: nome de órgãos, locais). |
| RF-ML-004 | Classificação Multi-label de Manifestações | O modelo de classificação deve receber um texto descritivo e retornar um conjunto de rótulos e suas respectivas probabilidades para as categorias Tipo de Manifestação, Órgão Responsável e Tema/Assunto. |
| RF-ML-005 | Classificação Binária para Score de Qualidade de Texto | O modelo de classificação deve receber o texto de uma manifestação e retornar um score numérico (0 a 100) que represente sua qualidade em termos de clareza e objetividade, com base em critérios pré-definidos. |
| RF-ML-006 | Clusterização de Tópicos em Conversas (Topic Modeling) | O sistema de ML deve ser capaz de processar um conjunto de logs de conversas anonimizados e agrupá-los em clusters temáticos, identificando os assuntos mais recorrentes. |
| RF-ML-007 | Coleta de Dados para Análise | O sistema deve ter uma rotina para coletar e anonimizar os dados de conversas, preparando-os para serem utilizados pelo modelo de clusterização. |

### 2.2. Requisitos Não Funcionais de ML (RNF-ML)

| **Código do req.** | **Nome** | **Descrição** |
|-|-|-|
| RNF-ML-001 | Precisão do Modelo de Classificação de Campos | O modelo de classificação multi-label (RF-ML-004) deve atingir uma métrica F1-Score média de no mínimo 0.85 no conjunto de dados de teste. |
| RNF-ML-002 | Consistência e Reprodutibilidade dos Modelos | Para uma mesma entrada, os modelos de ML devem produzir a mesma saída (inferência determinística). O processo de treinamento deve ser reprodutível. |
| RNF-ML-003 | Segurança Contra Injeção de Prompt | O sistema de interação com o LLM deve incluir mecanismos de validação e sanitização de entrada para mitigar riscos de manipulação por injeção de prompt. |
| RNF-ML-004 | Manutenibilidade da Base de Conhecimento (RAG) | Deve existir um processo definido para a atualização e reindexação da base de documentos do RAG, garantindo que o conhecimento do chatbot não fique obsoleto. |
| RNF-ML-005 | Monitoramento de Modelos | O sistema deve incluir monitoramento para acompanhar a performance dos modelos em produção, incluindo logs de inferência e métricas de acurácia, para detectar degradação ou desvios (drift). |
| RNF-ML-006 | Privacidade no Design dos Modelos | Os modelos devem ser treinados e operados seguindo os princípios de "Privacy by Design", garantindo que dados sensíveis sejam anonimizados antes do treinamento e que nenhuma informação pessoal seja retida ou exposta durante a inferência.
