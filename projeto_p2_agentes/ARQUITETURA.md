# Arquitetura e Documentação Técnica do Sistema

Este documento descreve a arquitetura, estrutura de módulos, contratos de dados, fluxo operacional determinístico e pontos de atenção do sistema multiagente baseado na API Google Gemini contido neste repositório.

A análise baseia-se estritamente no código-fonte, configurações e artefatos presentes no diretório `projeto_p2_agentes/`.

---

## 1. Visão Geral e Propósito

O sistema consiste em uma **plataforma determinística de orquestração multiagente em Python** projetada para automatizar o ciclo de desenvolvimento de software (SDLC) de uma aplicação web estática ("EcoCiclo Consultoria Ambiental e Gestão de Resíduos").

### Problema Resolvido
Elimina o comportamento estocástico ou caótico comum em cadeias de agentes autônomos por meio de:
1. **Controle determinístico de estados**: Uma máquina de estados síncrona implementada em Python puro (`main.py`), sem frameworks de caixa-preta.
2. **Contratos estruturados via JSON Schema**: Respostas estritamente tipadas e validadas programaticamente via SDK oficial `google-genai`.
3. **Auditoria de segurança e qualidade por separação de papéis**: O agente que codifica (Fullstack) não aprova sua própria entrega; a validação é conduzida por um agente independente (QA/Cibersegurança) com critérios rigorosos de segurança e acessibilidade.
4. **Proteção contra loops infinitos**: Teto estrito de iterações parametrizado via variável de ambiente (`MAX_RODADAS`).
5. **Observabilidade e telemetria completas**: Rastreamento em tempo real de latência, status de retries e contagem real de tokens (`usage_metadata`), consolidando os dados em logs e gerando relatórios formais em PDF (`fpdf2`).

---

## 2. Stack e Dependências Principais

### 2.1 Linguagem e Ambiente de Execução
- **Linguagem Principal**: Python 3.10+ (verificado suporte a anotações de tipo `from __future__ import annotations`; executável em Python 3.14 no ambiente virtual `.venv`).
- **Padrão de Execução**: Síncrono e determinístico, executado em linha de comando (CLI).

### 2.2 Bibliotecas e SDKs (Python)
Mapeadas a partir de `projeto_p2_agentes/requirements.txt`:
- **`google-genai>=1.0.0`**: SDK oficial do Google para integração com a família de modelos Gemini (usa `genai.Client`, `types.GenerateContentConfig`, `response_mime_type="application/json"` e `response_json_schema`).
- **`python-dotenv>=1.0.0`**: Leitura e injeção de variáveis de ambiente a partir do arquivo `.env`.
- **`fpdf2>=2.8.0`**: Mecanismo de renderização vetorial de relatórios acadêmicos e técnicos em formato PDF (`Documentacao_P2.pdf`).

### 2.3 Banco de Dados, Filas e Mensageria
- **Banco de Dados**: **Inexistente**. Não há banco relacional (SQL) nem orientado a documentos (NoSQL). Toda a persistência é baseada no sistema de arquivos local (`filesystem`).
- **Filas / Mensageria**: **Inexistente**. A comunicação entre agentes ocorre estritamente em memória por meio de retornos de função e estruturas tipadas em Python.

### 2.4 Stack da Aplicação Gerada (Front-end Estático)
Os arquivos gerados pelos agentes em `output/site/` utilizam exclusivamente padrões web nativos:
- **HTML5**: Semântico (`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`, `<form novalidate>`), sem frameworks externos.
- **CSS3**: Folha de estilos única (`style.css`), modular, mobile-first, com `@media queries` e suporte a `:focus-visible`. Sem dependência de Bootstrap, Tailwind ou CDNs.
- **JavaScript**: Vanilla JS seguro (`script.js`), utilizando exclusivamente `addEventListener` e manipulação de texto via `textContent` (prevenção nativa contra XSS). Não utiliza `innerHTML`, `outerHTML`, `eval` ou bibliotecas como jQuery/React.

---

## 3. Estrutura de Pastas e Módulos

```
.
├── ARQUITETURA.md                     # Documentação de arquitetura do sistema
└── projeto_p2_agentes/                # Módulo principal da aplicação multiagente
    ├── .env.example                   # Modelo das variáveis de ambiente
    ├── .env                           # Configurações locais ativas (chaves e modelos)
    ├── .gitignore                     # Ignora .venv, caches e arquivos sensíveis
    ├── requirements.txt               # Dependências Python do projeto
    ├── main.py                        # Orquestrador determinístico do fluxo
    ├── agentes.py                     # Integração com Gemini, schemas JSON e retries
    ├── logger.py                      # Observabilidade, telemetria de tokens e log
    ├── gerar_relatorio_pdf.py         # Extrator de métricas e gerador do PDF final
    ├── prompts/                       # Instruções e contratos de sistema
    │   ├── pedido_principal.txt       # Requisitos funcionais e técnicos da demanda
    │   ├── sys_coordenador.txt        # Prompt de sistema: Agente Coordenador
    │   ├── sys_fullstack.txt          # Prompt de sistema: Agente Fullstack
    │   └── sys_qa_sec.txt             # Prompt de sistema: Agente QA/Cibersegurança
    └── output/                        # Artefatos gerados pela execução
        ├── execucao_real.log          # Registro padronizado de eventos e métricas
        ├── docs/                      # Documentação gerada pelos agentes
        │   ├── plano_tarefas.md       # Plano técnico e requisitos críticos (Coordenador)
        │   ├── resumo_implementacao.md# Histórico de implementação/refatoração (Fullstack)
        │   └── parecer_qa.md          # Auditoria estática e veredito (QA/Cibersegurança)
        └── site/                      # Código-fonte da aplicação web gerada
            ├── index.html             # Estrutura HTML5 da página institucional
            ├── style.css              # Estilos visuais e regras responsivas
            └── script.js              # Validação do formulário e manipulação de DOM
```

### Responsabilidade Real dos Componentes

| Módulo / Arquivo | Responsabilidade Técnica |
|---|---|
| `main.py` | Ponto de entrada (`main()`). Carrega variáveis de ambiente, inicializa `Monitor`, lê a demanda em `prompts/pedido_principal.txt`, coordena o ciclo de rodadas (Coordenador -> Fullstack -> QA -> Gate Decisório) e grava os artefatos finais em disco. |
| `agentes.py` | Implementa a classe `EquipeAgentes` e a definição dos schemas JSON (`SCHEMA_COORDENADOR`, `SCHEMA_FULLSTACK`, `SCHEMA_QA_SEC`). Gerencia timeouts HTTP, tradução de códigos de erro de API, mecanismo de retry com backoff exponencial para erros transitórios (HTTP 429/503/timeout) e higienização de Markdown. |
| `logger.py` | Implementa a classe `Monitor`. Responsável pela telemetria em tempo real, sanitização de strings (remoção de sequências ANSI e caracteres de controle), gravação com flush atômico em `output/execucao_real.log` e impressão sincronizada em `sys.stdout`. |
| `gerar_relatorio_pdf.py` | Implementa a classe `RelatorioP2PDF` (extensão de `FPDF`). Lê `output/execucao_real.log`, faz o parse via regex de eventos e contagens de tokens, inspeciona estaticamente `output/site/` e os relatórios em `output/docs/`, compilando um relatório de 10 quesitos em `Documentacao_P2.pdf`. |
| `prompts/` | Diretório isolado contendo as instruções estáticas de engenharia de prompt (system instructions e contexto do pedido). |
| `output/` | Diretório de persistência de saída dos artefatos produzidos pelos agentes durante a execução da esteira. |

---

## 4. Fluxo de Funcionamento (End-to-End)

O sistema opera como uma **máquina de estados determinística finita**, alternando entre planejamento, codificação, auditoria estática e tomada de decisão lógica.

```mermaid
flowchart TD
    A([Início: main.py]) --> B[Carregar .env e validar GEMINI_API_KEY]
    B --> C[Ler prompts/pedido_principal.txt]
    C --> D[Inicializar Monitor e EquipeAgentes]
    
    subgraph Fase 0: Planejamento
        D --> E[Executar Agente Coordenador]
        E --> F[Validar SCHEMA_COORDENADOR]
        F --> G[Gravar output/docs/plano_tarefas.md]
    end
    
    subgraph Ciclo de Rodadas [Rodada 1 até MAX_RODADAS]
        G --> H[Executar Agente Fullstack]
        H --> I[Validar SCHEMA_FULLSTACK e limpar Markdown]
        I --> J[Gravar output/site/ e resumo_implementacao.md]
        J --> K[Executar Agente QA/Cibersegurança]
        K --> L[Validar SCHEMA_QA_SEC]
        L --> M[Gravar output/docs/parecer_qa.md]
        M --> N{Gate Decisório: aprovado == True && achados == []?}
    end
    
    N -- Sim --> O[Status: concluido_com_sucesso]
    N -- Não & Rodada < MAX_RODADAS --> P[Alimentar apontamentos_qa para Refatoração]
    P --> H
    N -- Não & Rodada >= MAX_RODADAS --> Q[Status: limite_rodadas_atingido]
    
    O --> R[Gravar Evento ENCERRAMENTO no Log]
    Q --> R
    R --> S([Fim da Orquestração])
    
    S -.->|Execução subsequente manual| T[py gerar_relatorio_pdf.py]
    T --> U([Documentacao_P2.pdf gerado])
```

### Detalhamento das Etapas

1. **Bootstrap e Validação**:
   - `main.py` carrega `.env` e valida a presença de `GEMINI_API_KEY`.
   - Lê `GEMINI_MODEL` (fallback para `gemini-3.8-flash` ou valor configurado) e `MAX_RODADAS` (fallback para 3).
   - Limpa `output/execucao_real.log` anterior e cria diretórios necessários.

2. **Fase 0 - Planejamento Técnico**:
   - O **Coordenador** recebe `pedido_principal.txt` combinado com `sys_coordenador.txt`.
   - Retorna um JSON estrito contendo: `resumo_planejamento`, `plano_tarefas_md` e `requisitos_criticos`.
   - O orquestrador salva `output/docs/plano_tarefas.md`.

3. **Fase 1..N - Ciclo de Codificação e Auditoria**:
   - **Agente Fullstack**:
     - *Rodada 1*: Recebe a demanda e o plano técnico.
     - *Rodadas 2..N*: Recebe a demanda, o plano, a lista de `apontamentos_qa` anteriores e o código gerado na rodada prévia (`codigo_anterior`).
     - Produz o código de `index.html`, `style.css` e `script.js` dentro da estrutura JSON.
     - O orquestrador remove eventuais cercas Markdown residuais (`_remover_cercas_markdown`) e grava os arquivos em `output/site/`.
   - **Agente QA/Cibersegurança**:
     - Recebe a demanda, o plano e o conteúdo atual dos três arquivos de código.
     - Executa auditoria estática contra um checklist rígido (WCAG, conformidade estrutural, ausência de CDNs/frameworks e ausência de `innerHTML`/`eval`).
     - Emite veredito booleano (`aprovado`), lista de pendências (`achados`) e texto detalhado (`parecer_qa_md`), salvo em `output/docs/parecer_qa.md`.

4. **Gate Decisório (Python Puro)**:
   - O orquestrador avalia a expressão:
     ```python
     if aprovado and not achados:
         status_final = "concluido_com_sucesso"
         break
     ```
   - Caso haja pendências e `rodada < max_rodadas`, retroalimenta o Fullstack.
   - Caso atinja `max_rodadas` com pendências, encerra com `"limite_rodadas_atingido"`.

5. **Compilação de Relatório**:
   - `gerar_relatorio_pdf.py` lê `output/execucao_real.log`, faz a extração de métricas de tokens (`usage_metadata`), analisa os arquivos em `output/site/` e `output/docs/`, compilando `Documentacao_P2.pdf`.

---

## 5. Modelo de Dados e Persistência

Não existe base de dados relacional ou transacional. A integridade dos dados e o estado da aplicação baseiam-se em contratos estruturados (**JSON Schemas**) transmitidos à API Gemini via `response_json_schema`.

### 5.1 Schemas de Dados Estruturados (`agentes.py`)

#### A. Contrato do Coordenador (`SCHEMA_COORDENADOR`)
```json
{
  "type": "object",
  "properties": {
    "resumo_planejamento": { "type": "string" },
    "plano_tarefas_md": { "type": "string" },
    "requisitos_criticos": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["resumo_planejamento", "plano_tarefas_md", "requisitos_criticos"]
}
```

#### B. Contrato do Fullstack (`SCHEMA_FULLSTACK`)
```json
{
  "type": "object",
  "properties": {
    "arquivos": {
      "type": "object",
      "properties": {
        "index_html": { "type": "string" },
        "style_css": { "type": "string" },
        "script_js": { "type": "string" }
      },
      "required": ["index_html", "style_css", "script_js"]
    },
    "resumo_implementacao_md": { "type": "string" },
    "correcoes_aplicadas": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["arquivos", "resumo_implementacao_md", "correcoes_aplicadas"]
}
```

#### C. Contrato do QA/Cibersegurança (`SCHEMA_QA_SEC`)
```json
{
  "type": "object",
  "properties": {
    "aprovado": { "type": "boolean" },
    "resumo_auditoria": { "type": "string" },
    "achados": {
      "type": "array",
      "items": { "type": "string" }
    },
    "parecer_qa_md": { "type": "string" }
  },
  "required": ["aprovado", "resumo_auditoria", "achados", "parecer_qa_md"]
}
```

### 5.2 Regras Críticas de Consistência e Aceite
- **Proibição estrita de manipulação insegura de DOM**: Proibido uso de `innerHTML`, `outerHTML`, `document.write` ou `eval`. Apenas `textContent` é autorizado.
- **Isolamento de dependências**: O código do site não pode importar scripts externos, CDNs ou estilos remotos.
- **Banner Acadêmico Literal**: Presença compulsória da mensagem informando o caráter demonstrativo e sem envio externo de dados.
- **Conformidade de Formulário**: Todos os campos obrigatórios associados a `<label for="...">` e validação de e-mail via regex no client-side.

---

## 6. Configuração, Execução e Pontos de Atenção

### 6.1 Variáveis de Ambiente

Configuradas via arquivo `projeto_p2_agentes/.env`:

| Variável | Obrigatória | Padrão no Código | Descrição |
|---|---|---|---|
| `GEMINI_API_KEY` | **Sim** | `None` (lança erro se ausente) | Chave de autenticação gerada no Google AI Studio. |
| `GEMINI_MODEL` | Não | `gemini-3.8-flash` (ou `gemini-3.5-flash-lite` no `.env.example`) | Modelo Gemini utilizado para todos os agentes. |
| `MAX_RODADAS` | Não | `3` | Teto máximo de ciclos Fullstack <-> QA. Inteiro >= 1. |
| `NOME_ALUNO` | Não | `"Equipe Acadêmica EcoCiclo (P2)"` | Nome inserido no cabeçalho do relatório `Documentacao_P2.pdf`. |

### 6.2 Instruções de Execução Local

No terminal (PowerShell no Windows ou Bash no Linux):

```powershell
# 1. Navegar até a pasta do projeto
cd C:\Codes\Code\Projetos\IARoubaEmpregoDeNoventaPorCentoDaAreaDeTI\projeto_p2_agentes

# 2. Criar e ativar o ambiente virtual (caso não exista)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
copy .env.example .env
# Editar .env preenchendo GEMINI_API_KEY=sua_chave_aqui

# 5. Executar o orquestrador multiagente
python main.py

# 6. Gerar o relatório consolidado em PDF
python gerar_relatorio_pdf.py
```

---

### 6.3 Débitos Técnicos, Acoplamentos e Gargalos Observados

1. **Acoplamento Temático Rígido nos Prompts de Sistema**:
   - Os prompts de sistema (`sys_coordenador.txt`, `sys_fullstack.txt`, `sys_qa_sec.txt`) contêm referências explícitas e regras rígidas atreladas ao tema "EcoCiclo Consultoria Ambiental" e à estrutura estrita de 3 arquivos (`index.html`, `style.css`, `script.js`). O sistema não é genérico para criação de qualquer projeto de software sem alteração manual dos arquivos de prompt.

2. **Auditoria Estática Baseada em LLM (Sem Linters Tradicionais)**:
   - A auditoria de QA e Cibersegurança é realizada pela própria inferência do LLM via prompt. Não há linters determinísticos em tempo de execução (como `ESLint`, `HTMLHint` ou ferramentas SAST automatizadas). Embora haja declaração explícita de limitação estática, a conformidade depende da capacidade de análise contextual do modelo Gemini escolhido.

3. **Crescimento do Payload de Contexto no Loop de Refatoração**:
   - A cada rodada de refatoração, o agente Fullstack recebe em seu prompt o código completo gerado na iteração anterior (`index.html`, `style.css` e `script.js`), juntamente com a lista de apontamentos de QA. Em aplicações maiores, essa estratégia causa rápido aumento no consumo de tokens de entrada (`prompt_token_count`), elevando latência e custo.

4. **Execução Síncrona e Ausência de Paralelismo**:
   - A orquestração é estritamente sequencial. Durante retries de API com backoff exponencial (`time.sleep`), a thread principal é bloqueada. O modelo atual atende com eficiência ao escopo sequencial proposto, mas impediria a paralelização de múltiplos agentes avaliadores (ex.: um agente especialista em acessibilidade e outro em cibersegurança executando simultaneamente).

5. **Tratamento de Codificação para Geração do PDF (`fpdf2`)**:
   - O gerador de PDF (`gerar_relatorio_pdf.py`) aplica sanitização forçada para caracteres em `latin-1` (`sanitizar_texto`) com substituição de caracteres especiais para evitar falhas no mecanismo de fontes nativas do `fpdf2`. A adoção de fontes TrueType (`.ttf`) com suporte nativo a UTF-8 simplificaria essa camada.

6. **Escopo do Repositório Global**:
   - O repositório contém apenas a pasta `projeto_p2_agentes/`. A integração com outros sistemas ou módulos externos é `[A verificar]` (não há dependências externas ou pipelines CI/CD configurados no repositório).
