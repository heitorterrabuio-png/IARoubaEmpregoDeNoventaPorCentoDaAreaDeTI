# Plano de Trabalho – PetCare 24h

## Visão Geral
- **Objetivo**: Criar site estático, responsivo, acessível (WCAG 2.1 nível AA básico) e seguro, contendo as seções exigidas e formulário de contato simulativo.
- **Entregáveis**: `output/site/index.html`, `output/site/style.css`, `output/site/script.js` e documentação em `output/docs/`.

## Divisão de Responsabilidades
| Agente | Tarefas Principais |
|--------|-------------------|
| **Fullstack** | 1. Estruturação semântica do HTML5 (lang, meta, header, nav, main, sections, footer).<br>2. Criação do CSS modular (mobile‑first, media queries, foco visível).<br>3. Implementação do JavaScript vanilla para validação do formulário (trim, regex e mensagens via `textContent`).<br>4. Geração dos arquivos de documentação preliminar (`plano_tarefas.md`, `resumo_implementacao.md`). |
| **QA / Cibersegurança** | 1. Análise estática do HTML, CSS e JS (lint, boas práticas, ausência de `innerHTML`, `eval`, URLs externas).<br>2. Verificação de acessibilidade (labels, aria‑live, ordem de tabulação, contraste).<br>3. Checagem de responsividade (breakpoints, overflow).<br>4. Emissão do parecer (`parecer_qa.md`) com lista de não‑conformidades e solicitações de ajuste. |

## Cronograma Simplificado (por rodada)
1. **Rodada 1 – Setup & Estrutura**
   - Fullstack cria esqueleto HTML, inclui meta tags, define IDs e âncoras.
   - QA revisa semântica e presença de `lang="pt-BR"`.
2. **Rodada 2 – Layout & Estilos**
   - Fullstack desenvolve `style.css` (mobile‑first, foco visível, contraste).<br>
   - QA verifica contraste (AA) e uso correto de `:focus-visible`.
3. **Rodada 3 – Interatividade**
   - Fullstack implementa `script.js` com validação, mensagens via `textContent` e `addEventListener`.
   - QA checa ausência de XSS, uso exclusivo de `textContent`, e que não há handlers inline.
4. **Rodada 4 – Revisão Final & Documentação**
   - QA executa auditoria completa, gera `parecer_qa.md`.
   - Fullstack corrige eventuais apontamentos e finaliza documentação (`resumo_implementacao.md`).

## Critérios de Aceite (Contrato de Entrega)
- **HTML**: Estrutura semântica completa, IDs e âncoras corretas, hierarquia de títulos sem pular níveis.
- **CSS**: Mobile‑first, sem overflow horizontal, foco visível com `:focus-visible`, contraste ≥ 4.5:1.
- **JS**: Validação de todos os campos, uso apenas de `textContent` para mensagens, `addEventListener` sem atributos inline, nenhum `innerHTML`/`eval`/URL externa.
- **Acessibilidade**: Labels associados, `aria-live="polite"` na região de feedback, navegação por Tab em ordem lógica.
- **Segurança**: Nenhum código vulnerável a XSS, nenhuma credencial ou chamada externa.
- **Documentação**: Todos os artefatos listados presentes em `output/site/` e `output/docs/`.

*Obs.: Caso algum critério não seja atendido, o QA abrirá uma nova rodada de correções até o limite máximo definido.*

## Requisitos Críticos Consolidados (Contrato de Aceite)

- HTML5 semântico com lang="pt-BR", charset UTF-8, viewport responsiva e hierarquia correta de headings (h1, h2, h3).
- Menu de navegação <nav> com links âncora funcionais para #inicio, #sobre, #servicos e #contato.
- Banner contendo exatamente o texto especificado sobre a natureza acadêmica da aplicação.
- Seção Início com <h1> e CTA que aponta para #contato ou #servicos.
- Seção Sobre Nós com <h2> e bloco de métricas (mínimo 3 indicadores).
- Seção Serviços com exatamente 3 <article> cards, cada um contendo <h3> com os títulos exigidos.
- Formulário de contato (<form novalidate>) com campos Nome, E‑mail, Assunto e Mensagem, todos associados a <label> via for/id.
- Botão de envio acessível e região de feedback com aria-live="polite".
- CSS modular, mobile‑first, sem uso de frameworks externos, contendo foco visível via :focus-visible e contraste de cores ≥ 4.5:1.
- JavaScript vanilla que valida campos (trim, regex de e‑mail), impede envio quando houver erro e exibe mensagens usando exclusivamente textContent.
- Nenhum handler inline no HTML; todos os eventos registrados com addEventListener no script.js.
- Proibição total de innerHTML, outerHTML, insertAdjacentHTML, document.write, eval e de qualquer chamada a APIs externas ou credenciais.
- Acessibilidade completa: navegação por teclado em ordem lógica, foco visível, labels corretas, aria-live para feedback.
- Entrega dos arquivos index.html, style.css, script.js em output/site/ e documentação (plano_tarefas.md, resumo_implementacao.md, parecer_qa.md) em output/docs/.
