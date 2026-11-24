"""Módulo de monitoramento, observabilidade e registro de execução multiagente."""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SEPARADOR = "=" * 72

NOMES: dict[str, str] = {
    "arquiteto": "ARQUITETO DE PROMPTS",
    "coordenador": "COORDENADOR",
    "fullstack": "FULLSTACK",
    "qa_sec": "QA/CIBERSEGURANCA",
    "qa_ciberseguranca": "QA/CIBERSEGURANCA",
    "orquestrador": "ORQUESTRADOR",
}

ETAPAS: dict[str, str] = {
    "arquiteto": "Arquitetura de Prompts e Adaptacao Tematica",
    "arquitetura_prompts": "Arquitetura de Prompts e Adaptacao Tematica",
    "planejamento": "Planejamento Inicial",
    "implementacao": "Implementacao Inicial Fullstack",
    "refatoracao": "Refatoracao Fullstack",
    "auditoria": "Auditoria Estatica de Qualidade e Seguranca",
}

_ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def limpar_texto(texto: Any) -> str:
    """Remove sequências ANSI e caracteres de controle preservando quebras úteis."""
    if texto is None:
        return ""
    bruto = str(texto).replace("\r\n", "\n").replace("\r", "\n")
    sem_ansi = _ANSI_ESCAPE_RE.sub("", bruto)
    sem_controle = _CONTROL_CHARS_RE.sub("", sem_ansi)
    return sem_controle.strip()


def formatar_tokens(tokens: dict[str, int] | int | None) -> str:
    """Formata contagens de tokens reais em uma string padronizada."""
    if tokens is None:
        return "prompt=0 | saida=0 | total=0"
    if isinstance(tokens, int):
        return f"total={tokens}"
    prompt_t = int(tokens.get("prompt", 0) or 0)
    saida_t = int(tokens.get("saida", 0) or 0)
    total_t = int(tokens.get("total", prompt_t + saida_t) or 0)
    return f"prompt={prompt_t} | saida={saida_t} | total={total_t}"


def _formatar_campo(chave: str, valor: Any) -> str:
    """Formata um par chave-valor lidando com strings multilinha."""
    if isinstance(valor, dict) and {"prompt", "saida", "total"}.issubset(valor.keys()):
        texto = formatar_tokens(valor)
    elif isinstance(valor, (list, tuple)):
        itens = [limpar_texto(item) for item in valor if limpar_texto(item)]
        texto = "\n".join(f"- {item}" for item in itens) if itens else "(nenhum)"
    else:
        texto = limpar_texto(valor)

    if not texto:
        texto = "-"

    linhas = texto.splitlines()
    if len(linhas) <= 1:
        return f"{chave}: {texto}"

    corpo = "\n".join(f"  {linha}" for linha in linhas)
    return f"{chave}:\n{corpo}"


class Monitor:
    """Registra eventos estruturados no terminal e em arquivo de log UTF-8."""

    def __init__(
        self,
        caminho_log: str | Path = "output/execucao_real.log",
        limpar_anterior: bool = True,
    ) -> None:
        """Inicializa o monitor garantindo o diretório de destino e o arquivo de log."""
        self.caminho_log = Path(caminho_log)
        self.caminho_log.parent.mkdir(parents=True, exist_ok=True)
        if limpar_anterior:
            self.caminho_log.write_text("", encoding="utf-8")

    def _escrever(self, bloco: str) -> None:
        """Grava o bloco no arquivo UTF-8 e imprime de forma segura em sys.stdout."""
        with self.caminho_log.open("a", encoding="utf-8") as arquivo:
            arquivo.write(bloco + "\n")
            arquivo.flush()

        encoding_stdout = getattr(sys.stdout, "encoding", None) or "utf-8"
        try:
            sys.stdout.write(bloco + "\n")
        except UnicodeEncodeError:
            seguro = bloco.encode(encoding_stdout, errors="replace").decode(
                encoding_stdout, errors="replace"
            )
            sys.stdout.write(seguro + "\n")
        sys.stdout.flush()

    def evento(self, tipo: str, **campos: Any) -> None:
        """Registra um evento genérico com separador padrão, timestamp UTC e campos."""
        agora_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        linhas = [
            SEPARADOR,
            f"[{agora_utc}] EVENTO: {limpar_texto(tipo).upper()}",
        ]
        for chave, valor in campos.items():
            linhas.append(_formatar_campo(str(chave), valor))
        linhas.append(SEPARADOR)
        self._escrever("\n".join(linhas))

    @staticmethod
    def _resolver_nome(agente: str) -> str:
        """Resolve identificador de agente pelo dicionário NOMES, preservando fallback."""
        chave = limpar_texto(agente)
        return NOMES.get(chave.lower(), chave)

    @staticmethod
    def _resolver_etapa(etapa: str) -> str:
        """Resolve identificador de etapa pelo dicionário ETAPAS, preservando fallback."""
        chave = limpar_texto(etapa)
        return ETAPAS.get(chave.lower(), chave)

    def agente_inicio(
        self,
        agente: str,
        origem: str,
        etapa: str,
        rodada: int,
        tarefa: str,
    ) -> None:
        """Anuncia o início da execução de um agente específico."""
        self.evento(
            "AGENTE_INICIO",
            agente=self._resolver_nome(agente),
            origem=origem,
            etapa=self._resolver_etapa(etapa),
            rodada=rodada,
            tarefa=tarefa,
        )

    def agente_entrega(
        self,
        agente: str,
        rodada: int,
        resumo: str,
        parecer: str,
        duracao: float,
        tokens: dict[str, int] | int,
    ) -> None:
        """Registra a entrega de um agente com resumo, parecer, tempo e tokens reais."""
        self.evento(
            "AGENTE_ENTREGA",
            agente=self._resolver_nome(agente),
            rodada=rodada,
            resumo=resumo,
            parecer=parecer,
            duracao_segundos=f"{duracao:.2f}s",
            tokens_reais=formatar_tokens(tokens),
        )

    def decisao_coordenador(
        self,
        status: str,
        regra: str,
        rodada: int,
        max_rodadas: int,
    ) -> None:
        """Registra a decisão determinística do Coordenador/orquestrador após o QA."""
        self.evento(
            "DECISAO_COORDENADOR",
            agente="Coordenador (Gate Deterministico)",
            status=status,
            regra_aplicada=regra,
            rodada=rodada,
            max_rodadas=max_rodadas,
        )

    def encerramento(
        self,
        status: str,
        rodadas: int,
        tokens_totais: dict[str, int] | int,
        duracao_total: float | None = None,
        total_chamadas: int | None = None,
    ) -> None:
        """Finaliza a execução declarando métricas totais e limites de verificação."""
        campos: dict[str, Any] = {
            "status_final": status,
            "rodadas_executadas": rodadas,
        }
        if total_chamadas is not None:
            campos["chamadas_api"] = total_chamadas
        if duracao_total is not None:
            campos["duracao_total_segundos"] = f"{duracao_total:.2f}s"
        campos["tokens_totais_reais"] = formatar_tokens(tokens_totais)
        campos["escopo_verificacao"] = (
            "Auditoria realizada exclusivamente por analise estatica de codigo "
            "(HTML5, CSS3 e JavaScript)."
        )
        campos["aviso_seguranca"] = (
            "A aplicacao web gerada em output/site/ NAO foi executada "
            "automaticamente no sistema operacional por questoes de seguranca."
        )
        self.evento("ENCERRAMENTO", **campos)

    def erro(self, agente: str, etapa: str, detalhe: str) -> None:
        """Registra erros operacionais ou de API no terminal e no log."""
        self.evento(
            "ERRO_EXECUCAO",
            agente=self._resolver_nome(agente),
            etapa=self._resolver_etapa(etapa),
            detalhe=detalhe,
        )
