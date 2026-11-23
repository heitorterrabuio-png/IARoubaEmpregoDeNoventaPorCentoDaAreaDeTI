# Plano de Trabalho - EcoCiclo Consultoria Ambiental

## 1. Visão Geral
Construção de uma aplicação web estática, responsiva, acessível e segura para a EcoCiclo, sem dependências externas ou frameworks.

## 2. Divisão de Tarefas
### Agente Fullstack
- Desenvolver o arquivo index.html seguindo HTML5 semântico (lang="pt-BR", head, header, nav, main, sections, article, footer) e hierarquia de títulos estrita (h1, h2, h3).
- Incluir o banner de aviso acadêmico e as seções #inicio, #sobre, #solucoes e #contato com os campos de formulário especificados.
- Desenvolver o style.css em abordagem mobile-first, com contraste adequado e :focus-visible nítido.
- Desenvolver o script.js com addEventListener, validações de preenchimento, regex para e-mail e manipulação segura de feedback usando estritamente textContent.

### Agente de QA/Cibersegurança
- Auditar a ausência absoluta de innerHTML, outerHTML, insertAdjacentHTML ou eval.
- Validar a acessibilidade básica (WCAG): navegação via teclado, associação correta de labels e atributos aria-live="polite".
- Validar a responsividade e a ausência de recursos externos, CDNs, ou credenciais/chaves de API no código.

## 3. Critérios de Aceite
- Formulário totalmente validado no cliente sem recarregar a página.
- Mensagens injetadas via textContent.
- Estrutura de diretórios exatamente em output/site/.

## Requisitos Críticos Consolidados (Contrato de Aceite)

- Uso exclusivo de textContent para atualização de DOM e mensagens de feedback no formulário, com proibição estrita de innerHTML.
- HTML5 semântico com hierarquia de cabeçalhos correta (h1, h2, h3) e lang="pt-BR".
- Acessibilidade garantida por navegação via Tab e estilos :focus-visible visíveis em todos os elementos interativos.
- Associação explícita de todos os campos de formulário com <label> através de id e for.
- Validação robusta em JavaScript vanilla com addEventListener para campos vazios e formato de e-mail.
- Presença obrigatória e literal do banner de aviso acadêmico em destaque.
- Zero dependências externas, frameworks, CDNs ou backend real.
