# Cronograma

A seguir, apresentamos o cronograma de desenvolvimento do Produto Mínimo Viável (MVP) do projeto OuvidorIA. O plano de trabalho está organizado em sprints semanais, começando em 18 de Outubro e culminando na entrega final do projeto em 1º de Dezembro de 2025. O objetivo é garantir um progresso constante e iterativo, com entregáveis claros a cada semana, focando na construção das funcionalidades essenciais para a primeira versão do nosso assistente.

Nossa estratégia de desenvolvimento adota uma abordagem RAG-first, focada em mitigar os riscos técnicos do projeto. Priorizamos a construção da fundação do nosso sistema: a coleta de dados, a criação da base de conhecimento vetorial e a validação do fluxo de resposta de IA através de uma API (chatbot headless). Somente após garantir que o nosso assistente é funcional e preciso, avançamos para o desenvolvimento da interface do usuário (UI) e a integração final. Esta metodologia garante que a proposta de valor central do produto seja tecnicamente viável antes de investirmos no trabalho de front-end.

| Semana | Período | Foco da Semana | Entregáveis da Semana | User Stories Atendidas |
|:-:|-|-|-|-|
| 1 | Sáb, 18/out - Dom, 26/out | Construção da Base de Conhecimento | - Scripts de coleta de dados (scraping) executados.<br>- Pipeline de limpeza e estruturação dos documentos.<br>- Base de conhecimento vetorial (_Vector Store_) v1 criada e populada. | - |
| 2 | Seg, 27/out - Dom, 02/nov | Desenvolvimento do Fluxo de Resposta | - Implementação da lógica de Retrieval (busca na base vetorial).<br>- Implementação da lógica de Generation (criação de prompt e chamada ao LLM).<br>- Testes do fluxo via scripts concluídos. | - |
| 3 | Seg, 03/nov - Dom, 09/nov | API e Validação do chatbot headless | - API do chatbot criada: Um endpoint recebe uma pergunta e retorna a resposta gerada pelo RAG.<br>- Validação completa do chatbot sem interface via Postman. | US-001 e US-002 (Validadas no Backend) |
| 4 | Seg, 10/nov - Dom, 16/nov | Início do Desenvolvimento da Interface (UI) | - Protótipo inicial da interface de chat desenvolvido.<br>- Início da integração da UI com a API do chatbot. | US-001 (Início do Frontend) |
| 5 | Seg, 17/nov - Dom, 23/nov | Integração Completa e Deploy | - Conexão final da interface de chat com a API do RAG.<br>- MVP completo (Frontend + Backend) implantado em ambiente de testes. | US-001 e US-002 (Completas e Integradas) |
| 6 | Seg, 24/nov - Dom, 30/nov | Testes de Usabilidade e Refinamento | - Realização de testes de integração com a interface.<br>- Coleta de feedback e refinamentos finais no frontend e nos prompts do RAG.<br>- Preparação da documentação e apresentação. | - |
| 7 | Seg, 01/dez   | Entrega Final | - Apresentação e entrega final do MVP do OuvidorIA. | - |
