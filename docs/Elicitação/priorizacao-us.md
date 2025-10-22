# Priorização das Histórias de Usuário

Para definir um escopo claro e garantir que a primeira versão do nosso produto entregue o máximo de valor possível, utilizamos o framework de priorização MoSCoW. Esta é uma técnica ágil que nos ajuda a classificar as funcionalidades, a partir de nossas Histórias de Usuário, em quatro categorias distintas, gerenciando as expectativas e focando os esforços da equipe de desenvolvimento. As categorias são:

- **Must-have (M):** Requisitos essenciais e inegociáveis. Se um item "Must-have" não for entregue, o lançamento do produto é considerado um fracasso. Eles formam o núcleo do nosso Produto Mínimo Viável (MVP).
- **Should-have (S):** Funcionalidades importantes, que agregam valor significativo, mas não são vitais para o funcionamento básico do produto. Em uma situação ideal, seriam incluídas, mas o lançamento pode ocorrer sem elas.
- **Could-have (C):** Itens desejáveis, considerados "nice to have". São melhorias ou funcionalidades de menor impacto que serão incluídas apenas se houver tempo e recursos disponíveis, sem comprometer a entrega dos itens mais importantes.
- **Won't-have (W):** Requisitos que foram explicitamente reconhecidos e acordados como fora do escopo para esta fase ou lançamento específico. Isso não significa que nunca serão feitos, mas sim que não serão abordados agora.

## Análise e Justificativa da Priorização

A tabela abaixo resume a aplicação do método MoSCoW às Histórias de Usuário definidas para o projeto. A decisão de priorização foi guiada pelo objetivo de construir um MVP que valide a proposta de valor central para a persona do Cidadão, garantindo uma base sobre a qual poderemos construir funcionalidades mais avançadas em iterações futuras.

### Discussão da Estratégia

- **Must-Have (Fundamentais):** As histórias US-01 (Iniciar conversa) e US-02 (Obter informações) são os pontos principais do OuvidorIA. Sem a capacidade de interagir com o chatbot e obter respostas para suas dúvidas, o produto não cumpre sua promessa mais fundamental para o cidadão. Portanto, todos os esforços iniciais devem se concentrar em garantir que esta experiência seja funcional, confiável e precisa.

- **Should-Have (Aprimoramento de Valor):** Uma vez que o cidadão consegue obter informações, o próximo passo para continuarmos a agregar valor é ajudar o usuário a se expressar melhor. As histórias US-05 (Avaliar qualidade do texto) e US-06 (Receber sugestões de melhoria) entram aqui. Elas representam um diferencial importante, transformando o chatbot que auxiliava em dúvidas em um assistente de escrita de manifestações. Embora o MVP possa ser lançado sem elas, sua inclusão na sequência enriqueceria a experiência do usuário.

- **Could-Have (Incrementos Futuros):** Nesta categoria, agrupamos funcionalidades auxiliares que podem ser adicionadas como incrementos posteriores. A sugestão automática de campos (US-03 e US-04) é uma funcionalidade mais complexa que, embora muito útil, não é essencial para que o usuário consiga submeter uma manifestação. Da mesma forma, o dashboard para gestores (US-07) entrega valor para nossa segunda persona. A estratégia aqui é primeiro validar e consolidar a experiência do Cidadão antes de desenvolver as ferramentas de análise para o Gestor Público.

| Código da US | Must | Should | Could | Won't have |
| :---  | :---: | :---: | :---: | :---: |
| US-01 | X     |       |       |       |
| US-02 | X     |       |       |       |
| US-03 |       |       | X     |       |
| US-04 |       |       | X     |       |
| US-05 |       | X     |       |       |
| US-06 |       | X     |       |       |
| US-07 |       |       | X     |       |
