"""Gerador do relatório acadêmico final Documentacao_P2.pdf a partir dos logs reais."""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR = Path(__file__).resolve().parent
DIR_OUTPUT = BASE_DIR / "output"
DIR_SITE = DIR_OUTPUT / "site"
DIR_DOCS = DIR_OUTPUT / "docs"
DIR_PROMPTS = BASE_DIR / "prompts"
CAMINHO_LOG = DIR_OUTPUT / "execucao_real.log"
CAMINHO_PDF = BASE_DIR / "Documentacao_P2.pdf"
SEPARADOR_LOG = "=" * 72

_SUBSTITUICOES_UNICODE: dict[str, str] = {
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u00ab": '"',
    "\u00bb": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
    "\u2014": "-",
    "\u2013": "-",
    "\u2012": "-",
    "\u2015": "-",
    "\u2212": "-",
    "\u2022": "*",
    "\u25aa": "*",
    "\u25ab": "*",
    "\u25e6": "*",
    "\u2023": "*",
    "\u2219": "*",
    "\u25cf": "*",
    "\u25cb": "*",
    "\u2026": "...",
    "\u00a0": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2009": " ",
    "\u200b": "",
    "\ufeff": "",
    "\u2192": "->",
    "\u2190": "<-",
    "\u2194": "<->",
    "\u21d2": "=>",
    "\u2265": ">=",
    "\u2264": "<=",
    "\u2260": "!=",
    "\u2248": "~",
    "\u2713": "[OK]",
    "\u2714": "[OK]",
    "\u2705": "[OK]",
    "\u2717": "[X]",
    "\u2718": "[X]",
    "\u274c": "[X]",
}


def sanitizar_texto(texto: Any) -> str:
    """Converte strings Unicode para texto seguro em latin-1 sem gerar falhas no fpdf2."""
    if texto is None:
        return ""

    normalizado = unicodedata.normalize("NFC", str(texto))
    normalizado = normalizado.replace("\r\n", "\n").replace("\r", "\n")

    for original, substituto in _SUBSTITUICOES_UNICODE.items():
        normalizado = normalizado.replace(original, substituto)

    caracteres_seguros: list[str] = []
    for ch in normalizado:
        codigo = ord(ch)
        if ch in ("\n", "\t") or 32 <= codigo <= 126 or 160 <= codigo <= 255:
            caracteres_seguros.append(ch)
            continue

        decomposto = unicodedata.normalize("NFKD", ch)
        base_filtrada = "".join(
            c
            for c in decomposto
            if not unicodedata.combining(c) and (32 <= ord(c) <= 126 or 160 <= ord(c) <= 255)
        )
        if base_filtrada:
            caracteres_seguros.append(base_filtrada)

    resultado = "".join(caracteres_seguros)
    return resultado.encode("latin-1", "replace").decode("latin-1")


def _quebrar_tokens_longos(texto: str, limite: int = 86) -> str:
    """Insere quebras suaves em palavras contínuas muito longas para proteger multi_cell."""
    linhas_finais: list[str] = []
    for linha in texto.splitlines():
        palavras = linha.split(" ")
        novas_palavras: list[str] = []
        for palavra in palavras:
            if len(palavra) <= limite:
                novas_palavras.append(palavra)
            else:
                partes = [palavra[i : i + limite] for i in range(0, len(palavra), limite)]
                novas_palavras.append(" ".join(partes))
        linhas_finais.append(" ".join(novas_palavras))
    return "\n".join(linhas_finais)


def _limpar_markdown_para_pdf(texto_md: str) -> list[tuple[str, str]]:
    """Converte Markdown simples em blocos estruturados para renderização limpa no PDF."""
    blocos: list[tuple[str, str]] = []
    for linha_bruta in texto_md.splitlines():
        linha = linha_bruta.strip()
        if not linha:
            continue
        if linha.startswith("### "):
            blocos.append(("subtitulo", linha[4:].strip()))
        elif linha.startswith("## "):
            blocos.append(("subtitulo", linha[3:].strip()))
        elif linha.startswith("# "):
            blocos.append(("subtitulo", linha[2:].strip()))
        elif linha.startswith("> "):
            limpa = re.sub(r"[`*]", "", linha[2:].strip())
            blocos.append(("destaque", limpa))
        elif linha.startswith(("- ", "* ")):
            limpa = re.sub(r"\*\*(.*?)\*\*", r"\1", linha[2:].strip())
            limpa = limpa.replace("`", "")
            blocos.append(("item", f"* {limpa}"))
        else:
            limpa = re.sub(r"\*\*(.*?)\*\*", r"\1", linha)
            limpa = limpa.replace("`", "")
            blocos.append(("paragrafo", limpa))
    return blocos


class RelatorioP2PDF(FPDF):
    """Documento PDF institucional com sanitização automática e layout consistente."""

    def __init__(self, subtitulo_cabecalho: str | None = None) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.subtitulo_cabecalho = (
            subtitulo_cabecalho
            or "Inteligência Artificial (P2) | Sistema Multiagente | Prof. Vladmir B. da Cruz"
        )
        self.set_margins(left=16, top=18, right=16)
        self.set_auto_page_break(auto=True, margin=16)

    def header(self) -> None:
        """Desenha o cabeçalho discreto a partir da página 2."""
        if self.page_no() == 1:
            return
        self.set_font("helvetica", style="I", size=8)
        self.set_text_color(90, 105, 95)
        self.set_x(self.l_margin)
        self.cell(
            w=self.epw,
            h=6,
            text=sanitizar_texto(self.subtitulo_cabecalho),
            align="R",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        y_linha = self.get_y()
        self.set_draw_color(200, 215, 205)
        self.line(self.l_margin, y_linha, self.w - self.r_margin, y_linha)
        self.ln(3)

    def footer(self) -> None:
        """Desenha a numeração de páginas no rodapé."""
        self.set_y(-13)
        self.set_font("helvetica", style="I", size=8)
        self.set_text_color(100, 110, 105)
        self.set_x(self.l_margin)
        self.cell(
            w=self.epw,
            h=8,
            text=sanitizar_texto(f"Página {self.page_no()} / {{nb}}"),
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.TOP,
        )

    def titulo_quesito(self, numero: int, titulo: str) -> None:
        """Renderiza o cabeçalho visual de um dos 10 quesitos do edital."""
        if self.get_y() > self.h - 42:
            self.add_page()
        self.ln(2)
        self.set_fill_color(24, 78, 55)
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", style="B", size=11.5)
        self.set_x(self.l_margin)
        self.multi_cell(
            w=self.epw,
            h=7.5,
            text=sanitizar_texto(f"Quesito {numero} - {titulo}"),
            fill=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(2)
        self.set_text_color(30, 35, 32)

    def subtitulo(self, texto: str) -> None:
        """Renderiza subtítulo interno de seção."""
        if self.get_y() > self.h - 26:
            self.add_page()
        self.set_font("helvetica", style="B", size=10)
        self.set_text_color(24, 78, 55)
        self.set_x(self.l_margin)
        self.multi_cell(
            w=self.epw,
            h=5.5,
            text=sanitizar_texto(_quebrar_tokens_longos(texto)),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.set_text_color(30, 35, 32)
        self.ln(0.5)

    def paragrafo(self, texto: str) -> None:
        """Renderiza parágrafo padrão sanitizado."""
        self.set_font("helvetica", style="", size=9.5)
        self.set_text_color(35, 40, 37)
        self.set_x(self.l_margin)
        self.multi_cell(
            w=self.epw,
            h=5.2,
            text=sanitizar_texto(_quebrar_tokens_longos(texto)),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(1.2)

    def item_lista(self, texto: str) -> None:
        """Renderiza item de lista com recuo limpo."""
        self.set_font("helvetica", style="", size=9.5)
        self.set_text_color(35, 40, 37)
        self.set_x(self.l_margin + 3)
        self.multi_cell(
            w=self.epw - 3,
            h=5.0,
            text=sanitizar_texto(_quebrar_tokens_longos(texto)),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(0.6)

    def caixa_destaque(self, titulo: str, texto: str) -> None:
        """Renderiza bloco destacado com fundo suave para avisos ou resumos."""
        if self.get_y() > self.h - 32:
            self.add_page()
        self.set_fill_color(238, 246, 241)
        self.set_draw_color(36, 108, 76)
        self.set_font("helvetica", style="B", size=9.5)
        self.set_text_color(24, 78, 55)
        self.set_x(self.l_margin)
        self.multi_cell(
            w=self.epw,
            h=6.0,
            text=sanitizar_texto(f" {titulo}"),
            border="LTR",
            fill=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.set_font("helvetica", style="", size=9.0)
        self.set_text_color(30, 35, 32)
        self.set_x(self.l_margin)
        self.multi_cell(
            w=self.epw,
            h=4.9,
            text=sanitizar_texto(_quebrar_tokens_longos(texto)),
            border="LBR",
            fill=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(2)

    def bloco_monoespacado(self, texto: str) -> None:
        """Renderiza trechos de log ou comandos em fonte monoespaçada."""
        self.set_fill_color(245, 246, 245)
        self.set_draw_color(205, 210, 207)
        self.set_font("courier", style="", size=7.8)
        self.set_text_color(30, 32, 31)
        self.set_x(self.l_margin)
        self.multi_cell(
            w=self.epw,
            h=4.2,
            text=sanitizar_texto(_quebrar_tokens_longos(texto, limite=90)),
            border=1,
            fill=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(2)

    def tabela_simples(self, cabecalhos: list[str], linhas: list[list[str]], larguras: list[float]) -> None:
        """Renderiza tabela compacta com suporte a quebra de página."""
        def desenhar_cabecalho() -> None:
            self.set_fill_color(224, 236, 229)
            self.set_text_color(20, 65, 45)
            self.set_font("helvetica", style="B", size=8.5)
            self.set_x(self.l_margin)
            for idx, titulo in enumerate(cabecalhos):
                self.cell(
                    w=larguras[idx],
                    h=6.5,
                    text=sanitizar_texto(titulo),
                    border=1,
                    fill=True,
                    new_x=XPos.RIGHT if idx < len(cabecalhos) - 1 else XPos.LMARGIN,
                    new_y=YPos.TOP if idx < len(cabecalhos) - 1 else YPos.NEXT,
                )

        desenhar_cabecalho()
        self.set_font("helvetica", style="", size=8.2)
        self.set_text_color(35, 40, 37)

        for linha in linhas:
            if self.get_y() > self.h - 24:
                self.add_page()
                desenhar_cabecalho()
                self.set_font("helvetica", style="", size=8.2)
                self.set_text_color(35, 40, 37)

            self.set_x(self.l_margin)
            for idx, celula in enumerate(linha):
                texto_limpo = sanitizar_texto(celula)
                limite_chars = max(12, int(larguras[idx] * 0.55))
                if len(texto_limpo) > limite_chars:
                    texto_limpo = texto_limpo[: limite_chars - 3] + "..."
                self.cell(
                    w=larguras[idx],
                    h=6.0,
                    text=texto_limpo,
                    border=1,
                    new_x=XPos.RIGHT if idx < len(linha) - 1 else XPos.LMARGIN,
                    new_y=YPos.TOP if idx < len(linha) - 1 else YPos.NEXT,
                )
        self.ln(2.5)

    def renderizar_markdown(self, conteudo_md: str) -> None:
        """Renderiza conteúdo Markdown dinâmico lido dos artefatos gerados."""
        for tipo, texto in _limpar_markdown_para_pdf(conteudo_md):
            if tipo == "subtitulo":
                self.subtitulo(texto)
            elif tipo == "destaque":
                self.caixa_destaque("Nota do Documento", texto)
            elif tipo == "item":
                self.item_lista(texto)
            else:
                self.paragrafo(texto)


def _validar_artefatos_obrigatorios() -> list[Path]:
    """Verifica se todos os artefatos produzidos pelo main.py existem e têm conteúdo."""
    obrigatorios = [
        CAMINHO_LOG,
        DIR_DOCS / "plano_tarefas.md",
        DIR_DOCS / "resumo_implementacao.md",
        DIR_DOCS / "parecer_qa.md",
    ]
    ausentes = [p for p in obrigatorios if not p.is_file() or p.stat().st_size == 0]
    return ausentes


def _parsear_tokens_string(texto: str) -> dict[str, int]:
    """Extrai contagens numéricas de uma linha de tokens no formato do Monitor."""
    padrao = {
        "prompt": r"prompt=(\d+)",
        "saida": r"saida=(\d+)",
        "total": r"total=(\d+)",
    }
    resultado = {"prompt": 0, "saida": 0, "total": 0}
    for chave, regex in padrao.items():
        match = re.search(regex, texto)
        if match:
            resultado[chave] = int(match.group(1))
    return resultado


def _parsear_log_execucao(conteudo_log: str) -> dict[str, Any]:
    """Extrai blocos de eventos, métricas e linha do tempo de execucao_real.log."""
    blocos_brutos = [
        bloco.strip()
        for bloco in conteudo_log.split(SEPARADOR_LOG)
        if bloco.strip()
    ]
    eventos: list[dict[str, Any]] = []
    for bloco in blocos_brutos:
        linhas = bloco.splitlines()
        cabecalho = linhas[0].strip()
        match_cab = re.match(r"^\[(.*?)\]\s+EVENTO:\s+(.*)$", cabecalho)
        if not match_cab:
            continue

        timestamp, tipo_evento = match_cab.group(1).strip(), match_cab.group(2).strip()
        campos: dict[str, str] = {}
        chave_atual: str | None = None

        for linha in linhas[1:]:
            if linha.startswith("  ") and chave_atual is not None:
                campos[chave_atual] = f"{campos[chave_atual]}\n{linha[2:]}"
            elif ":" in linha:
                chave, valor = linha.split(":", 1)
                chave_atual = chave.strip()
                campos[chave_atual] = valor.strip()

        eventos.append(
            {
                "timestamp": timestamp,
                "tipo": tipo_evento,
                "campos": campos,
            }
        )

    info: dict[str, Any] = {
        "eventos": eventos,
        "modelo": "Não identificado no log",
        "modo_demanda": "Baseline Padrao (EcoCiclo)",
        "max_rodadas": "-",
        "status_final": "Não identificado no log",
        "rodadas_executadas": "-",
        "chamadas_api": "-",
        "duracao_total": "-",
        "tokens_totais": {"prompt": 0, "saida": 0, "total": 0},
        "entregas": [],
        "arquiteto_ativo": False,
        "arquiteto_tarefa": "",
        "arquiteto_resumo": "",
        "arquiteto_tema": "",
        "arquiteto_provedor": "",
        "contingencia_groq_ativa": False,
        "contingencia_provedor": "",
        "contingencia_motivo": "",
    }

    for ev in eventos:
        tipo = ev["tipo"]
        campos = ev["campos"]
        if tipo == "INICIO_ORQUESTRACAO":
            info["modelo"] = campos.get("modelo_gemini", info["modelo"])
            info["modo_demanda"] = campos.get("modo_demanda", info["modo_demanda"])
            info["max_rodadas"] = campos.get("max_rodadas", info["max_rodadas"])
        elif tipo == "CONTINGENCIA":
            prov = campos.get("provedor", "")
            if "groq" in prov.lower():
                info["contingencia_groq_ativa"] = True
                info["contingencia_provedor"] = prov or "Groq"
                info["contingencia_motivo"] = campos.get(
                    "motivo", "Gemini instável (503/429/overloaded)"
                )
        elif tipo == "AGENTE_INICIO":
            agente_ev = campos.get("agente", "")
            if "arquiteto de prompts" in agente_ev.lower():
                info["arquiteto_ativo"] = True
                info["arquiteto_tarefa"] = campos.get("tarefa", info["arquiteto_tarefa"])
        elif tipo == "AGENTE_ENTREGA":
            agente_ev = campos.get("agente", "-")
            if "arquiteto de prompts" in agente_ev.lower():
                info["arquiteto_ativo"] = True
                resumo_arq = campos.get("resumo", "")
                parecer_arq = campos.get("parecer", "")
                info["arquiteto_resumo"] = resumo_arq
                match_tema = re.search(r"Tema definido:\s*([^|\n]+)", resumo_arq, re.IGNORECASE)
                if match_tema:
                    info["arquiteto_tema"] = match_tema.group(1).strip()
                match_prov = re.search(r"Provedor:\s*([^|\n]+)", parecer_arq, re.IGNORECASE)
                if match_prov:
                    prov_arq = match_prov.group(1).strip()
                    info["arquiteto_provedor"] = prov_arq
                    if "groq" in prov_arq.lower():
                        info["contingencia_groq_ativa"] = True
                        info["contingencia_provedor"] = info["contingencia_provedor"] or prov_arq
            info["entregas"].append(
                {
                    "timestamp": ev["timestamp"],
                    "agente": agente_ev,
                    "rodada": campos.get("rodada", "-"),
                    "duracao": campos.get("duracao_segundos", "-"),
                    "tokens": campos.get("tokens_reais", "-"),
                    "parecer": campos.get("parecer", "-"),
                }
            )
        elif tipo == "ENCERRAMENTO":
            info["status_final"] = campos.get("status_final", info["status_final"])
            info["rodadas_executadas"] = campos.get(
                "rodadas_executadas", info["rodadas_executadas"]
            )
            info["chamadas_api"] = campos.get("chamadas_api", info["chamadas_api"])
            info["duracao_total"] = campos.get(
                "duracao_total_segundos", info["duracao_total"]
            )
            info["tokens_totais"] = _parsear_tokens_string(
                campos.get("tokens_totais_reais", "")
            )

    return info


def _inspecionar_site_estatico() -> dict[str, Any]:
    """Coleta métricas estáticas reais sobre os arquivos em output/site/ sem executá-los."""
    arquivos = ["index.html", "style.css", "script.js"]
    inventario: list[list[str]] = []
    verificacoes: dict[str, bool] = {
        "banner_academico": False,
        "focus_visible": False,
        "media_query": False,
        "usa_text_content": False,
        "sem_inner_html": True,
    }

    for nome in arquivos:
        caminho = DIR_SITE / nome
        if caminho.is_file():
            conteudo = caminho.read_text(encoding="utf-8", errors="replace")
            linhas = len(conteudo.splitlines())
            bytes_arq = caminho.stat().st_size
            inventario.append([nome, f"{bytes_arq} bytes", f"{linhas} linhas", "Presente"])

            if nome == "index.html":
                verificacoes["banner_academico"] = (
                    "aplicação acadêmica demonstrativa" in conteudo.lower()
                    or "aplicacao academica demonstrativa" in conteudo.lower()
                )
            elif nome == "style.css":
                verificacoes["focus_visible"] = ":focus-visible" in conteudo
                verificacoes["media_query"] = "@media" in conteudo
            elif nome == "script.js":
                verificacoes["usa_text_content"] = "textContent" in conteudo
                verificacoes["sem_inner_html"] = "innerHTML" not in conteudo
        else:
            inventario.append([nome, "0 bytes", "0 linhas", "Ausente"])
            if nome == "script.js":
                verificacoes["sem_inner_html"] = False

    return {"inventario": inventario, "verificacoes": verificacoes}


def _selecionar_trechos_log(conteudo_log: str, max_linhas: int = 44) -> str:
    """Seleciona trechos literais representativos do início e do encerramento do log."""
    linhas = [linha for linha in conteudo_log.splitlines() if linha.strip()]
    if len(linhas) <= max_linhas:
        return "\n".join(linhas)
    metade = max_linhas // 2
    cabeca = "\n".join(linhas[:metade])
    cauda = "\n".join(linhas[-metade:])
    return f"{cabeca}\n... [trecho intermediario omitido; ver output/execucao_real.log completo] ...\n{cauda}"


def gerar_pdf() -> int:
    """Constrói e salva o arquivo Documentacao_P2.pdf na raiz do projeto."""
    load_dotenv(dotenv_path=BASE_DIR / ".env")

    ausentes = _validar_artefatos_obrigatorios()
    if ausentes:
        print("\n[AVISO] Artefatos reais da execução não encontrados ou vazios:")
        for caminho in ausentes:
            print(f"  - {caminho}")
        print(
            "\nExecute o orquestrador primeiro para gerar os dados reais:\n"
            "  py main.py   (ou python main.py)\n"
        )
        return 1

    conteudo_log = CAMINHO_LOG.read_text(encoding="utf-8")
    dados_log = _parsear_log_execucao(conteudo_log)
    plano_md = (DIR_DOCS / "plano_tarefas.md").read_text(encoding="utf-8")
    resumo_impl_md = (DIR_DOCS / "resumo_implementacao.md").read_text(encoding="utf-8")
    parecer_qa_md = (DIR_DOCS / "parecer_qa.md").read_text(encoding="utf-8")
    dados_site = _inspecionar_site_estatico()

    nome_aluno = os.getenv("NOME_ALUNO", "Equipe Acadêmica P2").strip()
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")

    arquiteto_ativo = bool(dados_log["arquiteto_ativo"])
    if arquiteto_ativo:
        tema_aplicacao = (
            dados_log["arquiteto_tema"]
            or "Aplicação Web Dinamizada via Arquiteto de Prompts"
        )
        modo_descricao = (
            "Dinamizada via Agente Arquiteto de Prompts (metaprompting e clonagem da baseline)"
        )
        subtitulo_pdf = (
            "Inteligência Artificial (P2) | Sistema Multiagente Dinâmico | Prof. Vladmir B. da Cruz"
        )
    else:
        tema_aplicacao = "EcoCiclo Consultoria Ambiental e Gestão de Resíduos"
        modo_descricao = "Baseline EcoCiclo Padrão (prompts/pedido_principal.txt)"
        subtitulo_pdf = (
            "Inteligência Artificial (P2) | Sistema Multiagente EcoCiclo | Prof. Vladmir B. da Cruz"
        )

    pdf = RelatorioP2PDF(subtitulo_cabecalho=subtitulo_pdf)
    pdf.alias_nb_pages()

    # Capa / Cabeçalho Institucional
    pdf.add_page()
    pdf.set_fill_color(20, 68, 47)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", style="B", size=17)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        w=pdf.epw,
        h=11,
        text=sanitizar_texto(
            "TRABALHO PRÁTICO P2 - SISTEMA MULTIAGENTE EM PYTHON\n"
            f"Aplicação Web: {tema_aplicacao}"
        ),
        align="C",
        fill=True,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln(5)

    pdf.caixa_destaque(
        "Dados Institucionais",
        (
            "Disciplina: Inteligência Artificial\n"
            "Professor: Vladmir B. da Cruz\n"
            f"Aluno(a) / Autor(a): {nome_aluno}\n"
            f"Data de Geração do Relatório: {data_geracao}\n"
            f"Tema da Aplicação Gerada: {tema_aplicacao}\n"
            f"Modo de Execução Detectado no Log: {modo_descricao}"
        ),
    )

    tokens_totais = dados_log["tokens_totais"]
    contingencia_groq = bool(dados_log["contingencia_groq_ativa"])
    provedor_arquiteto = (
        dados_log["contingencia_provedor"]
        if contingencia_groq
        else (dados_log["arquiteto_provedor"] or f"Gemini ({dados_log['modelo']})")
    )
    linha_provedor_arq = ""
    if arquiteto_ativo:
        sufixo = " (Contingência Groq)" if contingencia_groq else ""
        linha_provedor_arq = f"Provedor do Arquiteto: {provedor_arquiteto}{sufixo}\n"

    pdf.caixa_destaque(
        "Resumo Executivo da Execução Real (Extraído de output/execucao_real.log)",
        (
            f"Modelo Configurado: {dados_log['modelo']}\n"
            f"Modo de Demanda: {modo_descricao}\n"
            f"{linha_provedor_arq}"
            f"Status Final da Orquestração: {dados_log['status_final']}\n"
            f"Rodadas Executadas / Limite: {dados_log['rodadas_executadas']} / {dados_log['max_rodadas']}\n"
            f"Chamadas Estruturadas à API: {dados_log['chamadas_api']}\n"
            f"Duração Total Observada: {dados_log['duracao_total']}\n"
            f"Tokens Reais Consumidos: prompt={tokens_totais['prompt']} | "
            f"saida={tokens_totais['saida']} | total={tokens_totais['total']}"
        ),
    )

    # Quesito 1
    pdf.titulo_quesito(1, "Tema Escolhido e Funcionalidades do Site Gerado")
    if arquiteto_ativo:
        pdf.paragrafo(
            "Conforme registrado em output/execucao_real.log, esta execução foi "
            "dinamizada via Agente Arquiteto de Prompts (ARQUITETO DE PROMPTS) por "
            "metaprompting e clonagem estrutural da baseline (prompts/pedido_principal.txt). "
            f"Tema adotado: {tema_aplicacao}."
        )
        if dados_log["arquiteto_resumo"]:
            pdf.caixa_destaque(
                "Especificação Temática Registrada pelo Arquiteto de Prompts",
                dados_log["arquiteto_resumo"],
            )
    else:
        pdf.paragrafo(
            "Conforme registrado em output/execucao_real.log, esta execução utilizou "
            "integralmente a baseline EcoCiclo padrão ('EcoCiclo Consultoria Ambiental e "
            "Gestão de Resíduos', prompts/pedido_principal.txt), direcionada a condomínios "
            "e pequenas e médias empresas (PMEs) para apresentação de serviços ambientais, "
            "métricas de impacto e contato demonstrativo."
        )
    pdf.paragrafo(
        "O site gerado em output/site/ reúne navegação semântica para as áreas "
        "temáticas definidas (mínimo de três áreas de conteúdo e seção de Contato), "
        "destaque obrigatório informando tratar-se de simulação acadêmica sem backend "
        "real, acessibilidade via teclado (Tab e :focus-visible), responsividade "
        "mobile-first e validação de formulário em JavaScript vanilla com manipulação "
        "segura de DOM baseada estritamente em textContent."
    )
    pdf.subtitulo("Inventário Real dos Arquivos Gerados em output/site/")
    pdf.tabela_simples(
        cabecalhos=["Arquivo", "Tamanho", "Linhas", "Status"],
        linhas=dados_site["inventario"],
        larguras=[48, 38, 38, 54],
    )

    # Quesito 2
    pdf.titulo_quesito(2, "Papéis e Responsabilidades dos Agentes")
    linhas_agentes = []
    if arquiteto_ativo:
        linhas_agentes.append(
            [
                "Arquiteto",
                "Clona baseline e adapta tema/guardrails via metaprompting.",
                "pedido_customizado.txt",
            ]
        )
    linhas_agentes.extend(
        [
            [
                "Coordenador",
                "Planeja etapas, define requisitos críticos e aplica o gate.",
                "plano_tarefas.md / decisao",
            ],
            [
                "Fullstack",
                "Codifica e refatora HTML5, CSS3 e JS vanilla seguro.",
                "index.html, style.css, script.js",
            ],
            [
                "QA/Ciberseg.",
                "Audita estaticamente semântica, WCAG, XSS e contrato.",
                "parecer_qa.md (aprovado/achados)",
            ],
        ]
    )
    pdf.tabela_simples(
        cabecalhos=["Agente", "Responsabilidade Principal", "Saída / Artefato"],
        linhas=linhas_agentes,
        larguras=[35, 92, 51],
    )
    if arquiteto_ativo:
        pdf.paragrafo(
            "O Arquiteto de Prompts traduz a ideia do usuário semileigo em uma "
            "especificação formal clonada da baseline; o Coordenador não gera código-fonte "
            "web; o Fullstack não autoaprova suas entregas; e o QA/Cibersegurança atua "
            "exclusivamente por análise estática."
        )
    else:
        pdf.paragrafo(
            "O Coordenador não gera código-fonte da aplicação web; o Fullstack não "
            "autoaprova suas entregas; e o QA/Cibersegurança atua exclusivamente por "
            "análise estática, devolvendo achados objetivos quando há não conformidades. "
            "(O Agente Arquiteto de Prompts opcional permaneceu inativo nesta execução baseline.)"
        )

    # Quesito 3
    pdf.titulo_quesito(3, "Protocolo de Comunicação e Máquina de Estados em Python")
    pdf.paragrafo(
        "A orquestração é determinística em Python puro (main.py), sem frameworks de "
        "caixa-preta. Cada chamada à biblioteca oficial google-genai utiliza "
        "response_mime_type='application/json' e response_json_schema (sem a chave "
        "'additionalProperties': false) para garantir contratos tipados (SCHEMA_COORDENADOR, "
        "SCHEMA_FULLSTACK e SCHEMA_QA_SEC), parseados via json.loads."
    )
    pdf.item_lista("* Estado 1 (PLANEJAMENTO): Coordenador gera plano_tarefas.md e requisitos críticos.")
    pdf.item_lista("* Estado 2 (IMPLEMENTAÇÃO / REFATORAÇÃO): Fullstack cria ou ajusta os 3 arquivos web.")
    pdf.item_lista("* Estado 3 (AUDITORIA ESTÁTICA): QA/Cibersegurança verifica código contra o contrato.")
    pdf.item_lista(
        "* Estado 4 (GATE DETERMINÍSTICO): Se aprovado == True e achados == [], encerra "
        "como 'concluido_com_sucesso'. Caso contrário, retorna ao Fullstack até o teto MAX_RODADAS."
    )
    pdf.subtitulo("Síntese do Plano Produzido na Execução (output/docs/plano_tarefas.md)")
    pdf.renderizar_markdown("\n".join(plano_md.splitlines()[:22]))

    # Quesito 4
    pdf.titulo_quesito(4, "Estrutura e Estratégia dos Prompts Utilizados")
    if arquiteto_ativo:
        pdf.paragrafo(
            "Os registros em output/execucao_real.log comprovam que esta execução foi "
            "dinamizada via Agente Arquiteto de Prompts por metaprompting e clonagem da "
            "baseline (prompts/pedido_principal.txt). O prompt sys_arquiteto.txt gerou "
            "uma nova especificação temática (prompts/pedido_customizado.txt e cópia em "
            "output/docs/pedido_customizado.txt) preservando integralmente os guardrails "
            "técnicos, enquanto os prompts de sistema do Coordenador, Fullstack e QA "
            "operam de forma desacoplada do tema."
        )
        if contingencia_groq:
            pdf.paragrafo(
                "Observou-se ainda resiliência operacional de nível de produção: diante "
                "de falha transitória na API primária Gemini, o sistema ativou o fallback "
                f"automatizado via {provedor_arquiteto} para concluir o metaprompting do "
                "Arquiteto de Prompts sem interromper a esteira multiagente."
            )
        else:
            pdf.paragrafo(
                f"Provedor que atendeu o Agente Arquiteto nesta execução: {provedor_arquiteto}."
            )
        catalogo_prompts = [
            ("sys_arquiteto.txt", "Metaprompting e clonagem estrutural da baseline"),
            ("pedido_principal.txt", "Modelo estrutural de referência (baseline preservada)"),
            ("pedido_customizado.txt", "Especificação temática gerada dinamicamente"),
            ("sys_coordenador.txt", "Planejamento técnico e critérios de aceite (desacoplado)"),
            ("sys_fullstack.txt", "Codificação HTML5/CSS3/JS puro e refatoração (desacoplado)"),
            ("sys_qa_sec.txt", "Checklist estático de QA, WCAG e segurança (desacoplado)"),
        ]
    else:
        pdf.paragrafo(
            "Os registros em output/execucao_real.log confirmam a execução da baseline "
            "EcoCiclo padrão: a demanda foi lida diretamente de prompts/pedido_principal.txt "
            "sem acionamento do Agente Arquiteto de Prompts, orquestrada com prompts de "
            "sistema desacoplados por papel (sys_coordenador.txt, sys_fullstack.txt e "
            "sys_qa_sec.txt) e contratos estritos via schemas JSON."
        )
        catalogo_prompts = [
            ("pedido_principal.txt", "Baseline EcoCiclo: contrato funcional, banner e regras"),
            ("sys_coordenador.txt", "Planejamento técnico e critérios de aceite (desacoplado)"),
            ("sys_fullstack.txt", "Codificação HTML5/CSS3/JS puro e refatoração (desacoplado)"),
            ("sys_qa_sec.txt", "Checklist estático de QA, WCAG e segurança (desacoplado)"),
        ]
    linhas_prompts: list[list[str]] = []
    for nome_p, papel_p in catalogo_prompts:
        caminho_p = DIR_PROMPTS / nome_p
        if caminho_p.is_file():
            txt_p = caminho_p.read_text(encoding="utf-8")
            linhas_prompts.append([nome_p, f"{len(txt_p.splitlines())} linhas", papel_p])
        else:
            linhas_prompts.append([nome_p, "Ausente", papel_p])
    pdf.tabela_simples(
        cabecalhos=["Arquivo de Prompt", "Tamanho", "Estratégia / Escopo"],
        linhas=linhas_prompts,
        larguras=[48, 28, 102],
    )

    # Quesito 5
    pdf.titulo_quesito(5, "Guia de Instalação e Execução")
    pdf.paragrafo(
        "Para reproduzir a execução do sistema multiagente em ambiente Python local, "
        "siga os passos abaixo na raiz do diretório projeto_p2_agentes/:"
    )
    pdf.bloco_monoespacado(
        "1. Criar e ativar ambiente virtual:\n"
        "   python -m venv .venv  (ou py -m venv .venv)\n"
        "   .venv\\Scripts\\activate\n"
        "2. Instalar dependências:\n"
        "   pip install -r requirements.txt\n"
        "3. Configurar variáveis de ambiente:\n"
        "   Copiar .env.example para .env e preencher GEMINI_API_KEY\n"
        "4. Executar o sistema multiagente (baseline padrão EcoCiclo):\n"
        "   python main.py\n"
        "   (Opcional - Arquiteto de Prompts: python main.py --ideia \"Sua ideia\" ou --interativo)\n"
        "5. Gerar este relatório PDF a partir dos logs reais:\n"
        "   python gerar_relatorio_pdf.py"
    )

    # Quesito 6
    pdf.titulo_quesito(6, "Guia de Teste e Navegação Manual do Site")
    pdf.paragrafo(
        "Como a execução automatizada do código web no sistema operacional é bloqueada "
        "intencionalmente por segurança, a validação interativa do site gerado é feita "
        "manualmente pelo avaliador abrindo output/site/index.html em um navegador."
    )
    pdf.item_lista("* Navegação por Teclado: Pressionar Tab sequencialmente pelos links do menu, CTA e campos do formulário confirmando contorno visível (:focus-visible).")
    pdf.item_lista("* Responsividade: Redimensionar a janela para larguras mobile (~375px) e desktop (>= 1024px) verificando ausência de rolagem horizontal.")
    pdf.item_lista("* Validação do Formulário: Tentar enviar com campos vazios ou e-mail inválido e confirmar bloqueio com mensagem acessível; preencher todos os campos válidos para ver a confirmação simulada.")
    pdf.item_lista(
        f"* Inspeção Estática Rápida nos Arquivos Atuais: banner_academico={dados_site['verificacoes']['banner_academico']} | "
        f"focus_visible={dados_site['verificacoes']['focus_visible']} | "
        f"media_query={dados_site['verificacoes']['media_query']} | "
        f"usa_textContent={dados_site['verificacoes']['usa_text_content']} | "
        f"sem_innerHTML={dados_site['verificacoes']['sem_inner_html']}"
    )

    # Quesito 7
    pdf.titulo_quesito(7, "Linha do Tempo da Execução Real (Dados Extraídos do Log)")
    pdf.paragrafo(
        f"Os registros abaixo foram extraídos diretamente de output/execucao_real.log. "
        f"A execução contabilizou {dados_log['chamadas_api']} chamada(s) em "
        f"{dados_log['rodadas_executadas']} rodada(s), consumindo {tokens_totais['total']} "
        f"tokens totais ({tokens_totais['prompt']} de prompt e {tokens_totais['saida']} "
        f"de saída) em {dados_log['duracao_total']}."
    )
    if contingencia_groq:
        motivo_cont = dados_log["contingencia_motivo"] or "Gemini instável (503/429/overloaded)"
        pdf.caixa_destaque(
            "Resiliência Operacional - Contingência via Groq",
            (
                f"Provedor de Contingência Acionado: {provedor_arquiteto}\n"
                f"Motivo Registrado no Log: {motivo_cont}\n"
                "Avaliação: O sistema demonstrou resiliência operacional de nível de "
                "produção, ativando o fallback automatizado via Groq para contornar "
                "instabilidades transitórias de serviço da API primária sem perda da "
                "entrega ou quebra dos guardrails da P2."
            ),
        )
    if dados_log["entregas"]:
        linhas_entregas = [
            [
                e["timestamp"],
                e["agente"],
                e["rodada"],
                e["duracao"],
                e["tokens"],
            ]
            for e in dados_log["entregas"]
        ]
        pdf.tabela_simples(
            cabecalhos=["Timestamp UTC", "Agente", "Rod.", "Tempo", "Tokens Reais"],
            linhas=linhas_entregas,
            larguras=[40, 36, 14, 22, 66],
        )
    pdf.subtitulo("Trechos Literais de output/execucao_real.log")
    pdf.bloco_monoespacado(_selecionar_trechos_log(conteudo_log))

    # Quesito 8
    pdf.titulo_quesito(8, "Achados do QA/Cibersegurança e Refatorações do Fullstack")
    pdf.paragrafo(
        "Os blocos a seguir reproduzem dinamicamente o parecer estático emitido pelo "
        "agente de QA/Cibersegurança e o histórico de refatorações registradas pelo "
        "agente Fullstack durante a execução."
    )
    pdf.subtitulo("8.1 Parecer e Achados do QA/Cibersegurança (output/docs/parecer_qa.md)")
    pdf.renderizar_markdown(parecer_qa_md)
    pdf.subtitulo("8.2 Implementação e Correções Aplicadas (output/docs/resumo_implementacao.md)")
    pdf.renderizar_markdown(resumo_impl_md)

    # Quesito 9
    pdf.titulo_quesito(9, "Escopo Efetivamente Testado e Limitações Declaradas")
    pdf.caixa_destaque(
        "Declaração Obrigatória de Escopo e Limites de Segurança",
        (
            "1. Análise Estática Apenas: Toda a verificação automatizada do código web gerado "
            "foi realizada por inspeção estática pelo agente QA/Cibersegurança sobre HTML, CSS e JS.\n"
            "2. Não Execução Automática no SO: Os arquivos gerados em output/site/ NÃO foram "
            "executados automaticamente em navegador headless nem em subprocessos do sistema "
            "operacional por diretriz explícita de segurança.\n"
            "3. Ausência de Backend Real: O formulário de contato opera exclusivamente em "
            "memória/DOM no navegador do cliente para fins acadêmicos, sem envio externo de dados."
        ),
    )

    # Quesito 10
    pdf.titulo_quesito(10, "Declaração de Transparência sobre Ajustes Manuais")
    pdf.paragrafo(
        "A arquitetura de orquestração em Python (logger.py, agentes.py, main.py e "
        "gerar_relatorio_pdf.py) bem como os prompts de sistema em prompts/ foram "
        "projetados previamente para garantir controle determinístico de estado, "
        "observabilidade em tempo real e validação via schemas JSON."
    )
    pdf.paragrafo(
        "Todos os artefatos da aplicação web em output/site/ (index.html, style.css, "
        "script.js) e os documentos técnicos em output/docs/ foram gerados pelos "
        "agentes durante a execução registrada em output/execucao_real.log. Nenhum "
        "dado de métrica, token, achado ou parecer exibido neste relatório foi "
        "simulado manualmente após a execução."
    )

    pdf.output(str(CAMINHO_PDF))
    tamanho_kb = CAMINHO_PDF.stat().st_size / 1024.0
    print(f"\n[SUCESSO] Relatório gerado em: {CAMINHO_PDF} ({tamanho_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(gerar_pdf())
