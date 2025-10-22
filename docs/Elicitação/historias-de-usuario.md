# Histórias de Usuário

Nesta seção, detalhamos o escopo do projeto através de **Histórias de Usuário** (_User Stories_).

Uma História de Usuário é uma descrição simples e informal de uma funcionalidade, contada a partir da perspectiva de quem a deseja. É uma ferramenta central em metodologias ágeis que nos ajuda a focar no valor que entregamos ao usuário, seguindo o formato: **"Como um [tipo de usuário], eu quero [um objetivo], para que [um benefício]"**.

As histórias a seguir estão organizadas por módulos e descrevem as jornadas e funcionalidades planejadas para nossas duas personas principais: o **Cidadão**, em sua interação com o _chatbot_, e o **Gestor Público**, em sua análise de dados para a melhoria do serviço.

## **Módulo 1: Assistente de Informações (RAG)**

### US-01: Iniciar uma conversa com o assistente

- **Como um** Cidadão
- **Eu gostaria de** acessar o _chatbot_ e receber uma mensagem de boas-vindas
- **Para que** eu saiba que o sistema está pronto para me ajudar e entenda o seu propósito inicial.

**Critérios de Aceitação (CA):**

- **CA 1:** Ao abrir a interface do chat, uma mensagem de boas-vindas é exibida.
- **CA 2:** A interface do chat é limpa e intuitiva.
- **CA 3:** A interação inicial não solicita nenhuma informação pessoal.

**Requisitos Relacionados:** RF-PROD-001, RNF-PROD-001, RNF-PROD-004

---

### US-02: Obter informações sobre um procedimento da ouvidoria

- **Como um** Cidadão
- **Eu gostaria de** perguntar ao _chatbot_, em minhas próprias palavras, como realizar um procedimento (ex: "como faço uma denúncia?")
- **Para que** eu possa entender o processo de forma rápida e simples, sem precisar navegar por manuais complexos.

**Critérios de Aceitação (CA):**

- **CA 1:** Dado que eu pergunte sobre um procedimento, o sistema deve me retornar uma resposta em linguagem simples e acessível.
- **CA 2:** A resposta deve ser gerada e exibida na tela em menos de 5 segundos.
- **CA 3:** O sistema deve, quando aplicável, citar a fonte da informação (ex: "Fonte: Manual do Fala.BR, Seção 2.1").
- **CA 4:** A conversa não deve armazenar nenhuma informação de identificação pessoal minha, em conformidade com a LGPD.
- **CA 5:** A resposta deve ser gerada com base na base de conhecimento oficial e o sistema deve se recusar a responder perguntas fora deste escopo.
- **CA 6:** O sistema deve ser resistente a tentativas de manipulação por injeção de prompt.

**Requisitos Relacionados:** RF-PROD-002, RF-PROD-003, RNF-PROD-002, RNF-PROD-004, RF-ML-001, RF-ML-002, RNF-ML-003, RNF-ML-006

---

## **Módulo 2: Qualificação de Campos (Classificação)**

### US-03: Receber sugestões de campos para minha manifestação

- **Como um** Cidadão
- **Eu gostaria de** descrever o meu problema em texto livre
- **Para que** o sistema me ajude a categorizar minha manifestação corretamente, sugerindo o tipo, órgão e tema adequados.

**Critérios de Aceitação (CA):**

- **CA 1:** Após eu inserir a descrição do meu problema, a interface deve apresentar sugestões para os campos `Tipo de Manifestação`, `Órgão Responsável` e `Tema/Assunto`.
- **CA 2:** As sugestões devem ser geradas pelo modelo de classificação multi-label com uma precisão (F1-Score) mínima de 0.85.
- **CA 3:** A análise do texto e a apresentação das sugestões devem ocorrer em menos de 5 segundos.
- **CA 4:** O modelo deve extrair entidades relevantes (ex: nomes de órgãos citados) para refinar a sugestão.

**Requisitos Relacionados:** RF-PROD-004, RNF-PROD-002, RF-ML-003, RF-ML-004, RNF-ML-001

### US-04: Editar os campos sugeridos pelo assistente

- **Como um** Cidadão
- **Eu gostaria de** visualizar e poder modificar facilmente os campos que o assistente sugeriu
- **Para que** eu tenha controle total sobre a minha manifestação e possa corrigir qualquer sugestão que não esteja perfeitamente alinhada com a minha intenção.

**Critérios de Aceitação (CA):**

- **CA 1:** A interface deve exibir os campos sugeridos de forma clara (ex: em um formulário pré-preenchido).
- **CA 2:** Eu devo poder alterar qualquer valor sugerido usando menus suspensos ou campos de texto.
- **CA 3:** Eu devo poder limpar as sugestões e preencher os campos manualmente do zero.
- **CA 4:** A interface de edição deve ser intuitiva e acessível.

**Requisitos Relacionados:** RF-PROD-005, RNF-PROD-001

---

## **Módulo 3: Auxílio à Escrita (Qualidade da Manifestação)**

### US-05: Avaliar a qualidade do texto da minha manifestação

- **Como um** Cidadão
- **Eu gostaria de** submeter o texto que escrevi para uma análise de qualidade
- **Para que** eu possa ter uma avaliação objetiva da minha mensagem e saber se ela está clara o suficiente para ser compreendida pela ouvidoria.

**Critérios de Aceitação (CA):**

- **CA 1:** Deve haver um botão ou comando para "Analisar Qualidade do Texto".
- **CA 2:** Após a solicitação, o sistema deve exibir um "score de qualidade" (de 0 a 100) para o texto inserido.
- **CA 3:** A análise e a exibição do score devem ocorrer em menos de 5 segundos.
- **CA 4:** O score deve ser gerado pelo modelo de classificação binária treinado para este fim.

**Requisitos Relacionados:** RF-PROD-006, RNF-PROD-002, RF-ML-005

### US-06: Receber e aplicar sugestões de melhoria no texto

- **Como um** Cidadão
- **Eu gostaria de** ver sugestões práticas para melhorar meu texto, especialmente se a qualidade for considerada baixa
- **Para que** eu possa aprimorar minha manifestação, aumentando as chances dela ser resolvida de forma eficaz.

**Critérios de Aceitação (CA):**

- **CA 1:** Se o score de qualidade for inferior a um limiar pré-definido, o sistema deve apresentar uma lista de sugestões específicas.
- **CA 2:** As sugestões devem ser claras (ex: "Adicione a data do fato", "Seja mais específico sobre o local").
- **CA 3:** A interface deve permitir que eu veja as sugestões e escolha se quero aplicá-las ao meu texto original.
- **CA 4:** O sistema não deve alterar o sentido original da minha manifestação.

**Requisitos Relacionados:** RF-PROD-007, RF-PROD-008

---

## **Módulo 4: Análise de Dados (Analytics)**

### US-07: Visualizar os temas mais recorrentes das conversas

- **Como um** Gestor Público
- **Eu gostaria de** acessar um dashboard analítico protegido por login
- **Para que** eu possa entender, de forma visual e agregada, quais são as principais dúvidas e problemas enfrentados pelos cidadãos.

**Critérios de Aceitação (CA):**

- **CA 1:** O acesso ao dashboard deve ser restrito a usuários autenticados com o perfil "Gestor".
- **CA 2:** O dashboard deve exibir um gráfico ou nuvem de palavras com os principais tópicos identificados nas interações com o _chatbot_.
- **CA 3:** Todos os dados exibidos devem ser 100% anonimizados, sem qualquer vínculo com dados pessoais dos cidadãos.
- **CA 4:** Os dados devem ser processados por um modelo de clusterização para identificar os temas automaticamente.
- **CA 5:** O serviço do dashboard deve estar disponível 99.5% do tempo durante o horário comercial.

**Requisitos Relacionados:** RF-PROD-009, RNF-PROD-003, RNF-PROD-004, RF-ML-006, RF-ML-007
