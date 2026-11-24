# Plano de Trabalho - EcoCiclo Consultoria Ambiental

## Visão Geral
Desenvolvimento de aplicação web estática para a EcoCiclo, atendendo condomínios e PMEs com foco em sustentabilidade, métricas, serviços e formulário demonstrativo seguro.

## Divisão de Responsabilidades

### Agente Fullstack
- **Estrutura HTML (index.html):** Aplicação estrita de tags semânticas (<header>, <nav>, <main>, <section>, <article>, <footer>), lang='pt-BR', hierarquia rigorosa de títulos e inclusão do banner acadêmico obrigatório.
- **Estilização CSS (style.css):** Abordagem mobile-first, paleta verde institucional e off-white, sem CDNs externas, com suporte a :focus-visible e media queries.
- **Comportamento JS (script.js):** Validação de formulário via addEventListener, verificação estrita de campos obrigatórios e regex de e-mail, exibição de feedback via textContent (sem uso de innerHTML ou eval).

### Agente de QA/Cibersegurança
- **Auditoria de Acessibilidade:** Validação de foco por teclado, contraste de cores e associação correta de <label> para todos os campos.
- **Auditoria de Segurança (XSS/DOM):** Verificação rigorosa do uso exclusivo de textContent e ausência total de innerHTML ou injeções dinâmicas de código.
- **Conformidade:** Garantia de ausência de backend real, credenciais ou chamadas de API externas.

## Requisitos Críticos Consolidados (Contrato de Aceite)

- Uso exclusivo de textContent para manipulação de DOM no script.js, proibindo innerHTML, outerHTML e eval.
- Banner obrigatório com o texto acadêmico exato posicionado no topo e próximo ao formulário.
- Formulário com validação completa no navegador (campos obrigatórios e e-mail válido), exibindo mensagens de sucesso ou erro com aria-live='polite'.
- Navegação por teclado integral e visibilidade clara de foco (:focus-visible) em todos os elementos interativos.
- Estrutura semântica HTML5 correta com hierarquia estrita de títulos (h1, h2, h3) e ausência de CDNs ou frameworks externos.
