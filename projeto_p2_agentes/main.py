"""Orquestrador determinístico do sistema multiagente para geração web (P2)."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from agentes import EquipeAgentes, ErroExecucaoAgente
from logger import Monitor

BASE_DIR = Path(__file__).resolve().parent
DIR_PROMPTS = BASE_DIR / "prompts"
DIR_OUTPUT = BASE_DIR / "output"
DIR_SITE = DIR_OUTPUT / "site"
DIR_DOCS = DIR_OUTPUT / "docs"
CAMINHO_LOG = DIR_OUTPUT / "execucao_real.log"


def _ler_max_rodadas() -> int:
    """Lê MAX_RODADAS do ambiente garantindo inteiro >= 1."""
    bruto = os.getenv("MAX_RODADAS", "3").strip()
    try:
        valor = int(bruto)
        return max(1, valor)
    except ValueError:
        print(
            f"[AVISO] Valor inválido para MAX_RODADAS ('{bruto}'). Usando padrão 3."
        )
        return 3


def _acumular_tokens(acumulado: dict[str, int], novos: dict[str, int]) -> None:
    """Soma contagens reais de tokens ao total acumulado da execução."""
    acumulado["prompt"] += int(novos.get("prompt", 0) or 0)
    acumulado["saida"] += int(novos.get("saida", 0) or 0)
    acumulado["total"] += int(novos.get("total", 0) or 0)


def _formatar_plano_md(dados_plano: dict[str, Any]) -> str:
    """Consolida o plano de tarefas e os requisitos críticos em Markdown."""
    plano_md = str(dados_plano.get("plano_tarefas_md", "")).strip()
    requisitos = [str(r).strip() for r in dados_plano.get("requisitos_criticos", []) if str(r).strip()]
    bloco_req = "\n".join(f"- {item}" for item in requisitos) or "- Nenhum requisito listado."
    return (
        f"{plano_md}\n\n"
        "## Requisitos Críticos Consolidados (Contrato de Aceite)\n\n"
        f"{bloco_req}\n"
    )


def _formatar_resumo_implementacao_md(
    historico_rodadas: list[dict[str, Any]],
) -> str:
    """Consolida o resumo de implementação e as correções aplicadas por rodada."""
    ultima = historico_rodadas[-1]
    resumo_atual = str(ultima.get("resumo_implementacao_md", "")).strip()
    secoes_historico = []
    for entrada in historico_rodadas:
        rodada = entrada["rodada"]
        correcoes = entrada.get("correcoes_aplicadas") or []
        if correcoes:
            itens = "\n".join(f"- {item}" for item in correcoes)
        else:
            itens = "- Implementação inicial sem apontamentos prévios de QA."
        secoes_historico.append(f"### Rodada {rodada}\n{itens}")

    historico_md = "\n\n".join(secoes_historico)
    return (
        f"{resumo_atual}\n\n"
        "## Histórico de Implementação e Refatorações por Rodada\n\n"
        f"{historico_md}\n"
    )


def _formatar_parecer_qa_md(historico_qa: list[dict[str, Any]]) -> str:
    """Consolida o parecer final de QA com histórico de achados e aviso estático."""
    ultimo = historico_qa[-1]
    parecer_atual = str(ultimo.get("parecer_qa_md", "")).strip()
    aviso_estatico = (
        "Escopo e Limitação Declarada: Esta auditoria consiste exclusivamente em "
        "análise estática de código-fonte (HTML5, CSS3 e JavaScript). Nenhuma execução "
        "dinâmica em navegador ou execução automática no sistema operacional foi realizada."
    )
    if "estática" not in parecer_atual.lower() and "estatica" not in parecer_atual.lower():
        parecer_atual = f"{parecer_atual}\n\n> {aviso_estatico}"

    secoes_rodadas = []
    for entrada in historico_qa:
        rodada = entrada["rodada"]
        aprovado = "APROVADO" if entrada.get("aprovado") else "REPROVADO"
        achados = entrada.get("achados") or []
        if achados:
            itens = "\n".join(f"- {item}" for item in achados)
        else:
            itens = "- Nenhum achado ou não conformidade identificada."
        secoes_rodadas.append(f"### Rodada {rodada} ({aprovado})\n{itens}")

    historico_md = "\n\n".join(secoes_rodadas)
    return (
        f"{parecer_atual}\n\n"
        "## Histórico de Auditoria Estática por Rodada\n\n"
        f"{historico_md}\n"
    )


def _salvar_site(arquivos: dict[str, str]) -> None:
    """Grava os três arquivos estáticos gerados em output/site/."""
    mapeamento = {
        "index_html": DIR_SITE / "index.html",
        "style_css": DIR_SITE / "style.css",
        "script_js": DIR_SITE / "script.js",
    }
    for chave, destino in mapeamento.items():
        conteudo = str(arquivos.get(chave, ""))
        destino.write_text(conteudo, encoding="utf-8")


def _parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    """Interpreta as flags opcionais de linha de comando para customização temática."""
    parser = argparse.ArgumentParser(
        description=(
            "Orquestrador multiagente P2. Sem flags, executa a baseline padrão "
            "(prompts/pedido_principal.txt)."
        )
    )
    parser.add_argument(
        "--ideia",
        type=str,
        default=None,
        help="Ideia temática para gerar especificação customizada via Arquiteto de Prompts.",
    )
    parser.add_argument(
        "--interativo",
        action="store_true",
        help="Solicita interativamente a ideia temática no terminal via input().",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada do orquestrador multiagente P2."""
    args = _parsear_argumentos(argv)

    ideia_usuario: str | None = None
    if args.ideia is not None:
        ideia_usuario = args.ideia.strip()
        if not ideia_usuario:
            print(
                "\n[AVISO] A flag --ideia foi fornecida sem texto. "
                "Informe uma descrição não vazia ou execute 'python main.py' para a baseline padrão.\n"
            )
            return 1
    elif args.interativo:
        try:
            ideia_usuario = input(
                "Descreva a ideia da aplicação web que deseja gerar: "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[AVISO] Entrada interativa cancelada pelo usuário.\n")
            return 1
        if not ideia_usuario:
            print(
                "\n[AVISO] Nenhuma ideia informada no modo interativo. Encerrando sem alterar arquivos.\n"
            )
            return 1

    load_dotenv(dotenv_path=BASE_DIR / ".env")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print(
            "\n[ERRO DE CONFIGURAÇÃO] A variável GEMINI_API_KEY não foi encontrada.\n"
            "Para configurar:\n"
            "  1. Copie '.env.example' para '.env' na raiz de 'projeto_p2_agentes/'.\n"
            "  2. Preencha GEMINI_API_KEY=<sua_chave_google_ai_studio>.\n"
            "  3. Execute novamente: py main.py (ou python main.py).\n"
        )
        return 1

    modelo = (
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
        or "gemini-3.5-flash-lite"
    )
    max_rodadas = _ler_max_rodadas()

    DIR_SITE.mkdir(parents=True, exist_ok=True)
    DIR_DOCS.mkdir(parents=True, exist_ok=True)

    monitor = Monitor(CAMINHO_LOG)
    inicio_geral = time.perf_counter()
    tokens_totais = {"prompt": 0, "saida": 0, "total": 0}
    total_chamadas = 0

    caminho_pedido = DIR_PROMPTS / "pedido_principal.txt"
    if not caminho_pedido.is_file():
        monitor.erro(
            agente="Orquestrador",
            etapa="Leitura da Demanda",
            detalhe=f"Arquivo não encontrado: {caminho_pedido}",
        )
        return 1

    pedido_referencia = caminho_pedido.read_text(encoding="utf-8").strip()
    modo_demanda = (
        "Arquiteto de Prompts (Customizado)"
        if ideia_usuario
        else "Baseline Padrao (EcoCiclo)"
    )

    monitor.evento(
        "INICIO_ORQUESTRACAO",
        projeto="Sistema Multiagente P2 - Geracao Web Estruturada",
        modo_demanda=modo_demanda,
        modelo_gemini=modelo,
        max_rodadas=max_rodadas,
        politica_execucao=(
            "Analise estatica de codigo apenas; o codigo web gerado nao sera executado "
            "automaticamente no sistema operacional."
        ),
    )

    def _registrar_retry(
        agente: str, tentativa: int, max_tentativas: int, motivo: str, espera_s: int
    ) -> None:
        monitor.evento(
            "RETRY_CHAMADA",
            agente=agente,
            tentativa=f"{tentativa}/{max_tentativas}",
            motivo=motivo,
            espera_segundos=f"{espera_s}s",
        )

    try:
        equipe = EquipeAgentes(
            api_key=api_key,
            modelo=modelo,
            pasta_prompts=DIR_PROMPTS,
            on_retry=_registrar_retry,
        )

        # Etapa 0 (opcional via CLI): Agente Arquiteto de Prompts
        if ideia_usuario:
            monitor.agente_inicio(
                agente="arquiteto",
                origem="Usuario (CLI)",
                etapa="arquitetura_prompts",
                rodada=0,
                tarefa=(
                    "Clonar estrutura de pedido_principal.txt e adaptar especificação "
                    f"para a ideia: {ideia_usuario}"
                ),
            )
            try:
                res_arq = equipe.executar_arquiteto_prompts(ideia_usuario, pedido_referencia)
            except ErroExecucaoAgente as exc_arq:
                if equipe.groq_client is None:
                    motivo_sem_groq = (
                        "Fallback via Groq nao configurado (GROQ_API_KEY ausente no .env "
                        "ou biblioteca groq nao instalada)."
                    )
                    monitor.evento(
                        "CONTINGENCIA_NAO_CONFIGURADA",
                        agente="ARQUITETO DE PROMPTS",
                        detalhe=motivo_sem_groq,
                        erro_primario=str(exc_arq),
                    )
                    print(
                        "\n[DIAGNÓSTICO DE CONTINGÊNCIA] O provedor primário (Gemini) falhou:\n"
                        f"  {exc_arq}\n"
                        "O fallback automático via Groq não estava habilitado.\n"
                        "Dica: opcionalmente configure GROQ_API_KEY no arquivo .env "
                        "(e instale 'pip install -r requirements.txt') para ativar contingência automática.\n"
                    )
                monitor.erro(
                    agente="arquiteto",
                    etapa="arquitetura_prompts",
                    detalhe=str(exc_arq),
                )
                return 1

            provedor_arq = str(res_arq.get("provedor", f"Gemini ({modelo})"))
            if "groq" in provedor_arq.lower():
                monitor.evento(
                    "CONTINGENCIA",
                    agente="ARQUITETO DE PROMPTS",
                    provedor=provedor_arq,
                    motivo=(
                        equipe.ultimo_motivo_contingencia
                        or "Gemini instavel (503/429/overloaded)"
                    ),
                )

            total_chamadas += 1
            _acumular_tokens(tokens_totais, res_arq["tokens"])

            dados_arq = res_arq["dados"]
            demanda = str(dados_arq.get("pedido_estruturado_txt", "")).strip()
            (DIR_PROMPTS / "pedido_customizado.txt").write_text(
                demanda + "\n", encoding="utf-8"
            )
            (DIR_DOCS / "pedido_customizado.txt").write_text(
                demanda + "\n", encoding="utf-8"
            )

            areas = dados_arq.get("areas_tematicas") or []
            monitor.agente_entrega(
                agente="arquiteto",
                rodada=0,
                resumo=(
                    f"Tema definido: {dados_arq.get('tema_definido', '-')} | "
                    f"Público-alvo: {dados_arq.get('publico_alvo', '-')}"
                ),
                parecer=(
                    f"Provedor: {provedor_arq} | Especificação adaptada salva em "
                    f"prompts/pedido_customizado.txt e output/docs/pedido_customizado.txt "
                    f"({len(areas)} áreas temáticas)."
                ),
                duracao=res_arq["duracao"],
                tokens=res_arq["tokens"],
            )
        else:
            demanda = pedido_referencia

        # Etapa 1: Planejamento pelo Coordenador
        monitor.agente_inicio(
            agente="Coordenador",
            origem="Orquestrador (main.py)",
            etapa="Planejamento Inicial",
            rodada=0,
            tarefa="Analisar demanda principal e definir plano técnico e critérios de aceite.",
        )
        res_coord = equipe.executar_coordenador_planejamento(demanda)
        total_chamadas += 1
        _acumular_tokens(tokens_totais, res_coord["tokens"])

        dados_plano = res_coord["dados"]
        (DIR_DOCS / "plano_tarefas.md").write_text(
            _formatar_plano_md(dados_plano), encoding="utf-8"
        )

        monitor.agente_entrega(
            agente="Coordenador",
            rodada=0,
            resumo=dados_plano.get("resumo_planejamento", ""),
            parecer=(
                f"Plano gerado com {len(dados_plano.get('requisitos_criticos', []))} "
                "requisitos críticos definidos."
            ),
            duracao=res_coord["duracao"],
            tokens=res_coord["tokens"],
        )

        # Etapa 2: Loop determinístico Fullstack <-> QA/Cibersegurança
        codigo_atual: dict[str, str] | None = None
        apontamentos_qa: list[str] | None = None
        historico_implementacao: list[dict[str, Any]] = []
        historico_qa: list[dict[str, Any]] = []
        status_final = "limite_rodadas_atingido"
        rodadas_executadas = 0

        for rodada in range(1, max_rodadas + 1):
            rodadas_executadas = rodada

            if apontamentos_qa:
                tarefa_fs = (
                    f"Refatorar index.html, style.css e script.js corrigindo "
                    f"{len(apontamentos_qa)} apontamento(s) do QA."
                )
                origem_fs = "Coordenador / Apontamentos do QA"
                etapa_fs = "Refatoração Fullstack"
            else:
                tarefa_fs = "Gerar index.html, style.css e script.js completos conforme o plano."
                origem_fs = "Coordenador (Plano de Tarefas)"
                etapa_fs = "Implementação Inicial Fullstack"

            monitor.agente_inicio(
                agente="Fullstack",
                origem=origem_fs,
                etapa=etapa_fs,
                rodada=rodada,
                tarefa=tarefa_fs,
            )
            res_fs = equipe.executar_fullstack(
                demanda=demanda,
                plano=dados_plano,
                codigo_anterior=codigo_atual,
                apontamentos_qa=apontamentos_qa,
            )
            total_chamadas += 1
            _acumular_tokens(tokens_totais, res_fs["tokens"])

            dados_fs = res_fs["dados"]
            codigo_atual = dict(dados_fs["arquivos"])
            _salvar_site(codigo_atual)

            correcoes = [str(c).strip() for c in dados_fs.get("correcoes_aplicadas", []) if str(c).strip()]
            historico_implementacao.append(
                {
                    "rodada": rodada,
                    "resumo_implementacao_md": dados_fs.get("resumo_implementacao_md", ""),
                    "correcoes_aplicadas": correcoes,
                }
            )
            (DIR_DOCS / "resumo_implementacao.md").write_text(
                _formatar_resumo_implementacao_md(historico_implementacao),
                encoding="utf-8",
            )

            parecer_fs = (
                f"Arquivos gravados em output/site/ com {len(correcoes)} registro(s) "
                "de correção/implementação."
            )
            monitor.agente_entrega(
                agente="Fullstack",
                rodada=rodada,
                resumo=dados_fs.get("resumo_implementacao_md", "").splitlines()[0]
                if dados_fs.get("resumo_implementacao_md")
                else "Implementação concluída.",
                parecer=parecer_fs,
                duracao=res_fs["duracao"],
                tokens=res_fs["tokens"],
            )

            # Auditoria Estática pelo QA/Cibersegurança
            monitor.agente_inicio(
                agente="QA_Ciberseguranca",
                origem="Fullstack (output/site/)",
                etapa="Auditoria Estática de Qualidade e Segurança",
                rodada=rodada,
                tarefa=(
                    "Inspecionar estaticamente index.html, style.css e script.js "
                    "sem executar código no sistema operacional."
                ),
            )
            res_qa = equipe.executar_qa_sec(
                demanda=demanda,
                plano=dados_plano,
                arquivos_codigo=codigo_atual,
            )
            total_chamadas += 1
            _acumular_tokens(tokens_totais, res_qa["tokens"])

            dados_qa = res_qa["dados"]
            aprovado = bool(dados_qa.get("aprovado", False))
            achados = [str(a).strip() for a in dados_qa.get("achados", []) if str(a).strip()]

            historico_qa.append(
                {
                    "rodada": rodada,
                    "aprovado": aprovado,
                    "achados": achados,
                    "parecer_qa_md": dados_qa.get("parecer_qa_md", ""),
                }
            )
            (DIR_DOCS / "parecer_qa.md").write_text(
                _formatar_parecer_qa_md(historico_qa),
                encoding="utf-8",
            )

            parecer_curto_qa = (
                "APROVADO sem achados pendentes."
                if aprovado and not achados
                else f"REPROVADO com {len(achados)} achado(s) na análise estática."
            )
            monitor.agente_entrega(
                agente="QA_Ciberseguranca",
                rodada=rodada,
                resumo=dados_qa.get("resumo_auditoria", ""),
                parecer=parecer_curto_qa,
                duracao=res_qa["duracao"],
                tokens=res_qa["tokens"],
            )

            # Gate Determinístico do Coordenador
            if aprovado and not achados:
                status_final = "concluido_com_sucesso"
                monitor.decisao_coordenador(
                    status=status_final,
                    regra="aprovado == True e achados == []",
                    rodada=rodada,
                    max_rodadas=max_rodadas,
                )
                break

            apontamentos_qa = achados or [
                str(dados_qa.get("resumo_auditoria", "Correções solicitadas pelo QA."))
            ]
            if rodada < max_rodadas:
                monitor.decisao_coordenador(
                    status="reprovado_para_refatoracao",
                    regra="aprovado == False ou achados nao vazio; nova rodada autorizada",
                    rodada=rodada,
                    max_rodadas=max_rodadas,
                )
            else:
                status_final = "limite_rodadas_atingido"
                monitor.decisao_coordenador(
                    status=status_final,
                    regra="MAX_RODADAS atingido com pendencias remanescentes",
                    rodada=rodada,
                    max_rodadas=max_rodadas,
                )

        duracao_total = time.perf_counter() - inicio_geral
        monitor.encerramento(
            status=status_final,
            rodadas=rodadas_executadas,
            tokens_totais=tokens_totais,
            duracao_total=duracao_total,
            total_chamadas=total_chamadas,
        )

        print("\nArtefatos gerados:")
        print(f"  - Site estático: {DIR_SITE}")
        print(f"  - Documentação:  {DIR_DOCS}")
        print(f"  - Log detalhado: {CAMINHO_LOG}")
        print("Próximo passo: execute 'py gerar_relatorio_pdf.py' (ou 'python gerar_relatorio_pdf.py').")
        return 0

    except ErroExecucaoAgente as exc:
        monitor.erro(agente="EquipeAgentes", etapa="Chamada Gemini", detalhe=str(exc))
        return 1
    except KeyboardInterrupt:
        monitor.erro(
            agente="Orquestrador",
            etapa="Interrupção",
            detalhe="Execução interrompida pelo usuário.",
        )
        return 1
    except Exception as exc:
        monitor.erro(
            agente="Orquestrador",
            etapa="Falha Geral",
            detalhe=f"Erro inesperado: {exc}",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
