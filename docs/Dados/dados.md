# Coleta e Armazenamento de Dados

Este documento descreve as fontes de dados, o pipeline de ingestão/ETL, o armazenamento
vetorial e as decisões de engenharia de features adotadas pelo projeto.

## Fontes de Dados

- **Fala.BR (wiki / módulos):** páginas e documentos que descrevem tipos de manifestação
	e procedimentos. Objetivo: extrair módulos relacionados a pedidos de acesso à informação
	e manifestações correlatas.
- **Portais do Governo (atribuições / funções):** páginas oficiais que listam as funções
	e competências dos órgãos federais (ex.: páginas em gov.br ou perfis institucionais).
- **Uploads de usuários:** arquivos PDF/TXT enviados pela interface web.
- **Arquivos locais:** `ouvidorIA/data/raw/` (documentos fonte) e `ouvidorIA/data/processed/`
	(artefatos de ETL).

### Observações de conformidade

- Sempre respeitar `robots.txt` e limites de uso das APIs/portais ao fazer scraping.
- Registrar a origem (URL, timestamp) como metadado para cada documento coletado.

## Pipeline de Coleta e ETL

1. **Coleta / Scraping (concluído)**
	 - Observação: os scrapers para Fala.BR e para portais de órgãos já foram executados e
		 os resultados salvos em `ouvidorIA/data/raw/` e `ouvidorIA/data/processed/`.
	 - Caso seja necessário atualizar o dataset, reexecute os scrapers com cautela (respeitar
		 `robots.txt` e limites de uso) e armazene os artefatos em `data/raw/` (para novos
		 uploads) ou `data/processed/` (artefatos de ETL).
<!--	 - Frequência sugerida de atualização: conforme necessidade (semanal, quinzenal ou sob demanda). -->

2. **Limpeza e Normalização**
	 - Remover HTML desnecessário, normalizar acentuação, unificar formatos de datas e
		 campos de contato.
	 - Extrair metadados: `source_url`, `collected_at`, `doc_type`, `orgao` (quando aplicável).

3. **Chunking e Preparação para Embeddings**
	 - Dividir texto em chunks (ex.: 500 tokens / ~200-400 palavras) com overlap (10-20%) para
		 preservar contexto entre pedaços.
<!--	 - Incluir `metadata` por chunk: `source`, `page`, `orgao`, `topic`. -->

4. **Geração de Embeddings**
	 - Modelo de embeddings: configurável via `AppConfig.EMBED_MODEL_NAME` (ex.: Sentence-Transformers
		 multilingual model). Gerado com `HuggingFaceEmbedding` (LlamaIndex).

5. **Armazenamento Vetorial (Qdrant)**
	 - Vetores e payloads persistidos em Qdrant (pasta local `qdrant_data` em Docker).
	 - Indexação feita via `VectorStoreIndex.from_documents(...)` (LlamaIndex) e armazenada
		 na coleção definida por `AppConfig.COLLECTION_NAME`.

6. **Criação do Query Engine (RAG)**
	 - O índice vetorial é utilizado pelo `query_engine` que combina recuperação (R) com
		 geração (G) via o LLM (Ollama). O LLM é conectado antes de criar o query engine.

## Estrutura e Formatos de Armazenamento

- Diretórios principais:
	- `ouvidorIA/data/raw/` — documentos fonte (PDF, TXT, MD)
	- `ouvidorIA/data/processed/` — saídas ETL (TXT/MD limpos)
	- `qdrant_data/` — dados persistidos do Qdrant (volume Docker)
- Metadados por documento/chunk: `source_url`, `collected_at`, `doc_type`, `orgao`, `topic`, `hash`.

## Tipos de Manifestação e Funções dos Órgãos (conteúdo para RAG)

Objetivo: produzir textos explicativos e estruturados para alimentar a base de conhecimento
e melhorar a indicação de campos no formulário.

- **Tipos de manifestação** (exemplos e descrições curtas):
	- **Solicitação / Pedido de Informação**: pedido formal de acesso a documentos públicos.
	- **Reclamação**: manifestação sobre falha/insatisfação na prestação de serviço.
	- **Denúncia**: relato de irregularidade ou ilegalidade que pode exigir apuração.
	- **Sugestão / Elogio**: manifestações não adversas, para melhoria ou reconhecimento.

- **Funções dos órgãos (federais)**:
	- Para cada órgão incluir: `nome`, `missão`, `principais atribuições` e `exemplos de assuntos`
	- Exemplo: `Ministério da Saúde (MS)` — missão: formular políticas de saúde; atribuições:
		coordenação do SUS, vigilância sanitária, etc.

Esses textos devem ser armazenados como documentos (MD/TXT) e indexados para que o RAG
use esse contexto na hora de identificar órgãos e sugerir campos.

## Integração com o Frontend (campos `assunto` e `órgão`)

- Fonte dos dados: preferir APIs oficiais (Fala.BR) quando disponíveis; caso contrário,
	usar dataset extraído por scrapers e disponibilizado como JSON estático em `ouvidorIA/data/`.
<!-- - Implementação sugerida:
	- Servir arquivo `data/assuntos.json` e `data/orgaos.json` lidos pelo frontend na inicialização
		(cache em sessão e atualização periódica).
	- Alternativa: chamadas dinâmicas à API do Fala.BR com cache local e fallback para o arquivo
		estático quando offline. -->

## LLM / Prompting — Quando preencher campo vs responder chat

- Fluxo atual: `analyze_demand()` → `_classify_type()` → se `CHAT` retorna resposta;
	senão segue para identificação de órgão e geração de resumos.
- Problema observado: o LLM tende a sempre tentar preencher campos.

## Métricas de Sucesso e Monitoramento

- **Precisão de preenchimento**: % de campos sugeridos corretamente avaliados por auditoria manual.
- **Recall de recuperação**: fraction de documentos relevantes que aparecem nas respostas RAG.
- **Acurácia de identificação de órgão**: % de vezes que o órgão sugerido está correto.
- **Latência (p50/p95/p99)**: medição do tempo desde a pergunta até a resposta final.
- **Satisfação do usuário**: NPS / escala 1-5 após interação (se coletado).
- **Frescor do índice**: tempo desde a última atualização/coleção de dados.

<!--
## Como adicionar novos dados e reindexar

1. Para adicionar novos dados ou atualizações (inclusive novo scraping), coloque os arquivos
	(PDF/TXT/MD/JSON) em `ouvidorIA/data/raw/` ou em `ouvidorIA/data/processed/`.
2. Para reindexar do zero e garantir que os novos dados entrem no índice persistente do Qdrant,
	reinicie a aplicação com `FORCE_REBUILD_INDEX=true` (ex.: em Docker Compose) ou chame a
	função `ingest_and_index(force_rebuild=True)` na instância do `OuvidoriaRAGService`.
3. Recomenda-se incluir metadados para cada documento/artefato: `source_url`, `collected_at`,
	`doc_type`, `orgao` e `hash`. Isso ajuda na deduplicação e auditoria.
4. Se os scrapers forem reexecutados, mantenha controle de versão dos arquivos coletados e
	valide as diferenças antes de reindexar (scripts de comparação por `hash`/checksum são úteis).
-->