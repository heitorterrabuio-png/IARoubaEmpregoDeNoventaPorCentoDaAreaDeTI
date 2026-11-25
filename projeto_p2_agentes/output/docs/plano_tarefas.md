# Plano de Trabalho Técnico - Porsche Enthusiasts & Heritage Showcase

## 1. Visão Geral do Projeto
O projeto consiste na criação de um portal web estático, responsivo, acessível e seguro, voltado a entusiastas da Porsche. A aplicação contará com navegação por âncoras, apresentação histórica, métricas de desempenho, exibição de três modelos icônicos e um formulário de contato demonstrativo com validação estritamente no cliente.

---

## 2. Divisão de Responsabilidades

### 🛠️ Agente Fullstack (Implementação)
- **Estruturação HTML5 Semântico (`index.html`)**:
  - Implementar `<header>`, `<nav>`, `<main>`, `<section>`, `<article>` e `<footer>` com `lang="pt-BR"` e meta viewport.
  - Criar o banner de aviso acadêmico obrigatório visível com a mensagem literal exata.
  - Organizar a hierarquia rigorosa de títulos (`<h1>` em `#inicio`, `<h2>` em `#historia`, `#modelos` e `#contato`, `<h3>` nos artigos dos modelos).
  - Criar formulário acessível `<form novalidate>` com campos para nome, email, assunto e mensagem associados a `<label>` via `id`/`for` e área de feedback com `aria-live="polite"`.

- **Estilização CSS3 Modular (`style.css`)**:
  - Desenvolver layout mobile-first sem frameworks ou CDNs externas.
  - Definir paleta de cores institucional (vermelho Porsche racing, preto cadmiado, prata metálico e off-white) garantindo alto contraste.
  - Garantir visibilidade de foco com `:focus-visible` para acessibilidade via teclado.
  - Prevenir rolagem horizontal indesejada.

- **Lógica e Validação JS Vanilla (`script.js`)**:
  - Associar eventos utilizando exclusivamente `addEventListener` (sem handlers inline no HTML).
  - Implementar validação do formulário (verificação de campos vazios com `.trim()` e validação de e-mail via RegEx segura).
  - Exibir feedbacks de erro e sucesso usando ESTRITAMENTE `textContent` (proibido `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` ou `eval`).

### 🔒 Agente de QA & Cibersegurança (Auditoria Estática)
- **Auditoria de Segurança**:
  - Validar ausência total de APIs externas, credenciais, tokens ou envio real de dados.
  - Garantir inexistência de vetores de XSS (revisão rigorosa do uso exclusivo de `textContent`).
  - Verificar ausência de manipuladores de eventos inline (`onclick`, `onsubmit`, etc.).

- **Auditoria de Acessibilidade & Qualidade (WCAG)**:
  - Testar navegabilidade integral via teclado (tecla Tab) e ordem lógica de foco.
  - Verificar visibilidade dos indicadores `:focus-visible`.
  - Validar associação explícita entre `<label>` e inputs via `for`/`id` e presença de `aria-live="polite"`.
  - Confirmar responsividade sem quebra de layout ou rolagem horizontal.

---

## 3. Fluxo de Trabalho e Artefatos
1. **Fase 1**: Agente Fullstack cria a estrutura `output/site/index.html`, `style.css` e `script.js`.
2. **Fase 2**: Agente Fullstack gera `output/docs/resumo_implementacao.md` detalhando as escolhas técnicas.
3. **Fase 3**: Agente QA executa auditoria e gera `output/docs/parecer_qa.md` com status de aprovação ou correções necessárias.

---

## Requisitos Críticos Consolidados (Contrato de Aceite)

- Banner obrigatório visível no topo/área principal com o texto exato: 'Atenção: Este site é uma aplicação acadêmica demonstrativa. O formulário não possui backend real e nenhuma mensagem será enviada externamente.'
- Estrutura HTML5 semântica com lang='pt-BR', cabeçalho com menu de navegação funcional por âncora (#inicio, #historia, #modelos, #contato) e hierarquia estrita de títulos (h1 -> h2 -> h3) sem pular níveis.
- Seção #historia com trajetória histórica e métricas claras de desempenho (vitórias em Le Mans, aceleração Taycan 0-100 km/h e percentual de veículos em rodagem).
- Seção #modelos contendo exatamente 3 artigos (<article> com <h3>) para os modelos: Porsche 911, Porsche Taycan e Porsche 718 Cayman.
- Formulário de contato acessível (<form novalidate>) com labels associadas por id/for aos campos nome, email, assunto e mensagem, e container de feedback com aria-live='polite'.
- Estilização CSS3 pura mobile-first sem CDNs ou frameworks externos, com paleta de cores Porsche de alto contraste, foco visível via :focus-visible e zero rolagem horizontal.
- Script JS Vanilla sem manipuladores inline (uso de addEventListener), validação de campos vazios (.trim()) e e-mail com regex segura, utilizando ESTRITAMENTE textContent para inserção de mensagens (proibido innerHTML, outerHTML, insertAdjacentHTML, document.write ou eval).
- Ausência total de credenciais, tokens de API, bibliotecas externas ou envios HTTP externos no código.
