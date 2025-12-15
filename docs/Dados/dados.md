# Coleta e Armazenamento de Dados

Este documento descreve as fontes de dados, o pipeline de ingestão/ETL, o armazenamento
vetorial e as decisões de engenharia de features adotadas pelo projeto.

## Fontes de Dados

- **Fala.BR (wiki / módulos):** páginas e documentos que descrevem tipos de manifestação
	e procedimentos. Objetivo: extrair módulos relacionados a pedidos de acesso à informação
	e manifestações correlatas.
- **Documentos Governamentais:** documentos em formato PDF sobre leis/decretos, cartilhas, manuais, entre outros com informações sobre Ouvidoria Pública e a plataforma FalaBR.
- **Uploads de usuários:** arquivos PDF/TXT enviados pela interface web.


**Arquivos locais:** `ouvidorIA/data/raw/` (documentos fonte) e `ouvidorIA/data/processed/`
	(artefatos de ETL).


## Pipeline de Dados com ETL

Foi utilizado o processo de ETL para estruturação da pipeline de dados, pois os dados do projeto podem vir de fontes diversas (PDF, scraping, planilhas...).

1.**Extract (Extração)**

Nessa fase é realizada o scrapping das wikis do FalaBR, gerando uma estrutura JSON hierárquica baseado nos tópicos da wiki.

Algumas funcionalidades dessa fase são:
 
 * Blacklist de tópicos que não são extraídos, pois não são relevantes para o contexto da IA;
 * Links `<a>` são convertidos para formato Markdown (`[link](url)`) para melhor leitura pela LLM;
 * Utilização de hashing (MD5) no conteúdo extraído, assim somente os conteúdos que forem sendo alterados (hash diferente) são enviados para transformação e ingestão da LLM;
 * O contéudo extraído é salvo em `ouvidorIA/data/raw/` para fins de backup e auditoria.

2.**Transform (Transformação)**

Preparação dos dados coletados no scrapping para serem indexados no Banco Vetorial.

Técnicas aplicadas:

* **Flattening**: Transformação da árvore hierárquica do JSON em uma lista linear de tópicos. 

* **Breadcrumbs (Contexto)**: É adicionado o "caminho" no início de cada texto (ex: Wiki Ouvidoria > Ouvidoria > Prazos) para mapear a hierarquia dos tópicos, auxiliando na indexação e consumo pela LLM.

* **Chunking**: Fatiamento de textos longos em pedaços menores usando sobreposição (overlap) para que as frases não sejam cortadas ao meio ou percam o contexto.

Os dados são salvos em formato TXT em `ouvidorIA/data/processed/` para serem indexados no Banco Vetorial.

3.**Load (Carregamento)**

A fase final consiste no Embedding dos dados e salvamento no Banco Vetorial (Qdrant). O carregamento "puxa" os documentos fonte em formato PDF e TXT presentes em `ouvidorIA/data/raw/` e os dados processados de `ouvidorIA/data/processed/`.

* **Geração de Embeddings**: O modelo de embeddings pode ser configurado via `AppConfig.EMBED_MODEL_NAME` (ex.: Sentence-Transformers multilingual model). No projeto, foi utilizado o `HuggingFaceEmbedding` do LlamaIndex.

* **Armazenamento Vetorial (Qdrant)**:
	 - Vetores e payloads persistidos em Qdrant (pasta local `qdrant_data` em Docker).
	 - Indexação feita via `VectorStoreIndex.from_documents(...)` (LlamaIndex) e armazenada
		 na coleção definida por `AppConfig.COLLECTION_NAME`.


## Estrutura e Formatos de Armazenamento

### Diretórios principais
- `ouvidorIA/data/raw/` — documentos fonte (PDF, TXT, JSON)
- `ouvidorIA/data/processed/` — saídas ETL (TXT limpo)
- `qdrant_data/` — dados persistidos do Qdrant (volume Docker)

### JSON hierárquico (Scrapping)

* `sections`: contém todos os tópicos da wiki
* `topics`: faz a lógica de hierarquia dos tópicos, relacionando tópicos maiores com seus sub-tópicos

Exemplo: 
```json
{
	"wiki_name": "Wiki_Name",
	"wiki_url":"https://wiki.com/example",
	"version": "1.0",
	"sections": [
	  {
      "title": "Title 1",
      "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
      "topics": [ 
        {
          "title": "Subtitle 1",
          "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
          "topics": [
            ...
          ]
        },
        {
          "title": "Subtitle 2",
          "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
          "topics": [
            ...
          ]
        }
	    ]
		},
    {
      "title": "Title 2",
	    "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
	    "topics": [
        ...
      ]
    },
    ...
	]
}
```

### Arquivos de Texto (TXT) de dados processados

  * `## Contexto`: representa o "caminho" hierárquico (breadcrumbs), achatando a estrutura do JSON para dar contexto semântico imediato ao fragmento de texto.

  * Separador (`---`): delimita os chunks (blocos de texto) que serão vetorizados individualmente, garantindo a segmentação correta para o banco vetorial.

Exemplo:
```
## Contexto: Title 1 > Subtitle 1
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus lacinia odio vitae vestibulum vestibulum. 
Cras sed felis eget velit aliquet. Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus.

----------------------------------------
## Contexto: Title 1 > Subtitle 1 > Subtitle 1.1
Neque porro quisquam est qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit. Suspendisse potenti. 
Utle enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

----------------------------------------
## Contexto: Title 1 > Subtitle 2
Ut ultrices ultrices enim. Curabitur sit amet mauris. Morbi in dui quis est pulvinar ullamcorper. 
Nulla facilisi. Integer lacinia sollicitudin massa. Cras metus. Sed aliquet risus a tortor.
```