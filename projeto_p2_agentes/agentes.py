"""Definição de schemas JSON e interface com os agentes via google-genai."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

from google import genai
from google.genai import errors, types

SCHEMA_COORDENADOR: dict[str, Any] = {
    "type": "object",
    "properties": {
        "resumo_planejamento": {
            "type": "string",
            "description": "Síntese objetiva do plano de trabalho e critérios de aceite.",
        },
        "plano_tarefas_md": {
            "type": "string",
            "description": "Documento completo em Markdown detalhando o plano e divisão técnica.",
        },
        "requisitos_criticos": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Lista objetiva de requisitos críticos verificáveis pelo QA.",
        },
    },
    "required": ["resumo_planejamento", "plano_tarefas_md", "requisitos_criticos"],
}

SCHEMA_FULLSTACK: dict[str, Any] = {
    "type": "object",
    "properties": {
        "arquivos": {
            "type": "object",
            "properties": {
                "index_html": {
                    "type": "string",
                    "description": "Código HTML5 completo do arquivo index.html sem cercas Markdown.",
                },
                "style_css": {
                    "type": "string",
                    "description": "Código CSS3 completo do arquivo style.css sem cercas Markdown.",
                },
                "script_js": {
                    "type": "string",
                    "description": "Código JavaScript vanilla completo do arquivo script.js sem cercas Markdown.",
                },
            },
            "required": ["index_html", "style_css", "script_js"],
        },
        "resumo_implementacao_md": {
            "type": "string",
            "description": "Resumo técnico em Markdown da implementação ou refatoração.",
        },
        "correcoes_aplicadas": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Lista de correções realizadas (vazia se não houver apontamentos).",
        },
    },
    "required": ["arquivos", "resumo_implementacao_md", "correcoes_aplicadas"],
}

SCHEMA_QA_SEC: dict[str, Any] = {
    "type": "object",
    "properties": {
        "aprovado": {
            "type": "boolean",
            "description": "True somente se todas as regras funcionais, de acessibilidade e segurança passarem.",
        },
        "resumo_auditoria": {
            "type": "string",
            "description": "Síntese objetiva do resultado da análise estática de código.",
        },
        "achados": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Lista objetiva de falhas ou vulnerabilidades encontradas (vazia se aprovado).",
        },
        "parecer_qa_md": {
            "type": "string",
            "description": "Parecer técnico completo em Markdown declarando escopo estático sem execução dinâmica.",
        },
    },
    "required": ["aprovado", "resumo_auditoria", "achados", "parecer_qa_md"],
}

_CERCA_INICIO_RE = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*\n?")
_CERCA_FIM_RE = re.compile(r"\n?\s*```\s*$")


class ErroExecucaoAgente(RuntimeError):
    """Exceção levantada quando uma chamada a um agente falha de forma controlada."""


class EquipeAgentes:
    """Encapsula as chamadas estruturadas à API Gemini para os 3 agentes do projeto."""

    def __init__(
        self,
        api_key: str | None = None,
        modelo: str | None = None,
        pasta_prompts: str | Path | None = None,
        on_retry: Callable[[str, int, int, str, int], None] | None = None,
        timeout_segundos: int = 60,
    ) -> None:
        """Inicializa o cliente Gemini com timeout explícito e carrega os prompts."""
        chave = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        if not chave:
            raise ErroExecucaoAgente(
                "Chave GEMINI_API_KEY não fornecida para inicialização da equipe de agentes."
            )

        self.modelo = (
            modelo or os.getenv("GEMINI_MODEL", "gemini-3.8-flash") or "gemini-3.8-flash"
        ).strip()
        self.on_retry = on_retry
        self.timeout_segundos = max(1, int(timeout_segundos))
        self.pasta_prompts = (
            Path(pasta_prompts)
            if pasta_prompts is not None
            else Path(__file__).resolve().parent / "prompts"
        )
        self.client = self._criar_cliente(chave, self.timeout_segundos)

        self.sys_coordenador = self._ler_prompt("sys_coordenador.txt")
        self.sys_fullstack = self._ler_prompt("sys_fullstack.txt")
        self.sys_qa_sec = self._ler_prompt("sys_qa_sec.txt")

    @staticmethod
    def _criar_cliente(api_key: str, timeout_segundos: int) -> Any:
        """Cria o cliente genai.Client com HttpOptions(timeout=...) em milissegundos."""
        timeout_ms = timeout_segundos * 1000
        try:
            http_opts = types.HttpOptions(timeout=timeout_ms)
            return genai.Client(api_key=api_key, http_options=http_opts)
        except (AttributeError, TypeError):
            return genai.Client(api_key=api_key)

    def _ler_prompt(self, nome_arquivo: str) -> str:
        """Carrega o conteúdo de um arquivo de prompt em UTF-8."""
        caminho = self.pasta_prompts / nome_arquivo
        if not caminho.is_file():
            raise ErroExecucaoAgente(f"Arquivo de prompt não encontrado: {caminho}")
        return caminho.read_text(encoding="utf-8").strip()

    @staticmethod
    def _extrair_tokens(response: Any) -> dict[str, int]:
        """Extrai métricas reais de uso de tokens da resposta do Gemini."""
        uso = getattr(response, "usage_metadata", None)
        if uso is None:
            return {"prompt": 0, "saida": 0, "total": 0}
        prompt_tokens = int(getattr(uso, "prompt_token_count", 0) or 0)
        saida_tokens = int(getattr(uso, "candidates_token_count", 0) or 0)
        total_tokens = int(getattr(uso, "total_token_count", 0) or (prompt_tokens + saida_tokens))
        return {
            "prompt": prompt_tokens,
            "saida": saida_tokens,
            "total": total_tokens,
        }

    @staticmethod
    def _remover_cercas_markdown(codigo: str) -> str:
        """Remove cercas ```...``` caso o modelo as emita acidentalmente."""
        limpo = (codigo or "").strip()
        if limpo.startswith("```"):
            limpo = _CERCA_INICIO_RE.sub("", limpo, count=1)
            limpo = _CERCA_FIM_RE.sub("", limpo, count=1)
        return limpo.strip() + "\n"

    @staticmethod
    def _formatar_plano(plano: dict[str, Any] | str) -> str:
        """Normaliza o plano do Coordenador para texto de contexto."""
        if isinstance(plano, str):
            return plano.strip()
        resumo = str(plano.get("resumo_planejamento", "")).strip()
        plano_md = str(plano.get("plano_tarefas_md", "")).strip()
        requisitos = plano.get("requisitos_criticos", []) or []
        req_texto = "\n".join(f"- {item}" for item in requisitos)
        return (
            f"Resumo do Planejamento: {resumo}\n\n"
            f"Plano de Tarefas:\n{plano_md}\n\n"
            f"Requisitos Críticos:\n{req_texto}"
        ).strip()

    @staticmethod
    def _validar_campos_schema(
        nome_agente: str, dados: Any, campos_obrigatorios: list[str]
    ) -> dict[str, Any]:
        """Verifica se o JSON decodificado é um objeto contendo os campos obrigatórios."""
        if not isinstance(dados, dict):
            raise ErroExecucaoAgente(
                f"Resposta do agente {nome_agente} não retornou um objeto JSON válido."
            )
        faltantes = [campo for campo in campos_obrigatorios if campo not in dados]
        if faltantes:
            raise ErroExecucaoAgente(
                f"Resposta do agente {nome_agente} omitiu campos obrigatórios: {', '.join(faltantes)}"
            )
        return dados

    @staticmethod
    def _traduzir_erro_api(nome_agente: str, exc: errors.APIError) -> str:
        """Gera mensagem diagnóstica amigável para erros retornados pela API Gemini."""
        codigo = getattr(exc, "code", None)
        mensagem = getattr(exc, "message", None) or str(exc)
        if codigo in (401, 403):
            return (
                f"Falha de autenticação/permissão no agente {nome_agente} (HTTP {codigo}). "
                f"Verifique a chave GEMINI_API_KEY no arquivo .env. Detalhe: {mensagem}"
            )
        if codigo == 404:
            return (
                f"Modelo não encontrado para o agente {nome_agente} (HTTP 404). "
                f"Verifique GEMINI_MODEL no arquivo .env. Detalhe: {mensagem}"
            )
        if codigo == 429:
            return (
                f"Cota ou limite de requisições excedido no agente {nome_agente} (HTTP 429). "
                f"Aguarde alguns instantes ou verifique os limites da chave. Detalhe: {mensagem}"
            )
        if codigo == 503:
            return (
                f"Serviço Gemini temporariamente sobrecarregado ou indisponível para o agente "
                f"{nome_agente} (HTTP 503). Detalhe: {mensagem}"
            )
        if codigo == 400:
            return (
                f"Requisição inválida enviada ao agente {nome_agente} (HTTP 400). "
                f"Detalhe: {mensagem}"
            )
        return f"Erro da API Gemini no agente {nome_agente} (HTTP {codigo}): {mensagem}"

    @staticmethod
    def _eh_erro_transitorio_api(exc: errors.APIError) -> bool:
        """Identifica falhas transitórias da API Gemini passíveis de retry."""
        codigo = getattr(exc, "code", None)
        if codigo in (429, 503):
            return True
        texto = f"{getattr(exc, 'status', '')} {getattr(exc, 'message', '')} {exc}".lower()
        return any(
            termo in texto
            for termo in ("unavailable", "overloaded", "rate limit", "timeout", "timed out")
        )

    @staticmethod
    def _eh_erro_transitorio_geral(exc: Exception) -> bool:
        """Identifica timeouts ou falhas transitórias de transporte/rede."""
        if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
            return True
        texto = str(exc).lower()
        return any(
            termo in texto
            for termo in ("timeout", "timed out", "unavailable", "overloaded", "connection")
        )

    def _chamar_gemini(
        self,
        nome_agente: str,
        instrucao_sistema: str,
        conteudo_usuario: str,
        schema: dict[str, Any],
        temperatura: float = 0.2,
    ) -> dict[str, Any]:
        """Executa a chamada estruturada ao Gemini e retorna dados, tokens e duração."""
        config = types.GenerateContentConfig(
            system_instruction=instrucao_sistema,
            response_mime_type="application/json",
            response_json_schema=schema,
            temperature=temperatura,
        )

        max_tentativas = 3
        response = None
        inicio_total = time.perf_counter()

        for tentativa in range(1, max_tentativas + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.modelo,
                    contents=conteudo_usuario,
                    config=config,
                )
                break
            except errors.APIError as exc:
                codigo = getattr(exc, "code", None)
                if self._eh_erro_transitorio_api(exc) and tentativa < max_tentativas:
                    espera = 5 * (2 ** (tentativa - 1))
                    motivo = f"HTTP {codigo}" if codigo is not None else f"API transitória: {exc}"
                    if self.on_retry is not None:
                        self.on_retry(
                            nome_agente,
                            tentativa,
                            max_tentativas,
                            motivo,
                            espera,
                        )
                    time.sleep(espera)
                    continue
                raise ErroExecucaoAgente(self._traduzir_erro_api(nome_agente, exc)) from exc
            except Exception as exc:
                if self._eh_erro_transitorio_geral(exc) and tentativa < max_tentativas:
                    espera = 5 * (2 ** (tentativa - 1))
                    if self.on_retry is not None:
                        self.on_retry(
                            nome_agente,
                            tentativa,
                            max_tentativas,
                            f"Rede/Timeout: {exc}",
                            espera,
                        )
                    time.sleep(espera)
                    continue
                if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
                    raise ErroExecucaoAgente(
                        f"Erro de conexão/rede ao chamar o agente {nome_agente}: {exc}"
                    ) from exc
                raise ErroExecucaoAgente(
                    f"Falha inesperada ao comunicar com o agente {nome_agente}: {exc}"
                ) from exc

        duracao = time.perf_counter() - inicio_total

        texto_bruto = (getattr(response, "text", None) or "").strip()
        if not texto_bruto:
            raise ErroExecucaoAgente(
                f"O agente {nome_agente} retornou resposta vazia sem conteúdo JSON."
            )

        try:
            dados = json.loads(texto_bruto)
        except json.JSONDecodeError as exc:
            raise ErroExecucaoAgente(
                f"Falha ao fazer parse JSON da resposta do agente {nome_agente}: {exc}"
            ) from exc

        dados_validados = self._validar_campos_schema(
            nome_agente, dados, schema.get("required", [])
        )
        tokens = self._extrair_tokens(response)

        return {
            "dados": dados_validados,
            "tokens": tokens,
            "duracao": duracao,
        }

    def executar_coordenador_planejamento(self, demanda: str) -> dict[str, Any]:
        """Aciona o Coordenador para produzir o plano de trabalho e critérios de aceite."""
        prompt_usuario = (
            "Analise a demanda abaixo e elabore o plano de trabalho estruturado para a "
            "equipe (Fullstack e QA/Cibersegurança).\n\n"
            f"=== DEMANDA PRINCIPAL ===\n{demanda}"
        )
        return self._chamar_gemini(
            nome_agente="Coordenador",
            instrucao_sistema=self.sys_coordenador,
            conteudo_usuario=prompt_usuario,
            schema=SCHEMA_COORDENADOR,
            temperatura=0.2,
        )

    def executar_fullstack(
        self,
        demanda: str,
        plano: dict[str, Any] | str,
        codigo_anterior: dict[str, str] | None = None,
        apontamentos_qa: list[str] | None = None,
    ) -> dict[str, Any]:
        """Aciona o Fullstack para gerar ou refatorar index.html, style.css e script.js."""
        plano_texto = self._formatar_plano(plano)

        if apontamentos_qa and codigo_anterior:
            lista_achados = "\n".join(f"- {item}" for item in apontamentos_qa)
            prompt_usuario = (
                "Você deve REFATORAR a aplicação web corrigindo integralmente todos os "
                "apontamentos feitos pelo QA/Cibersegurança.\n\n"
                f"=== DEMANDA PRINCIPAL ===\n{demanda}\n\n"
                f"=== PLANO DO COORDENADOR ===\n{plano_texto}\n\n"
                f"=== APONTAMENTOS DO QA A CORRIGIR ===\n{lista_achados}\n\n"
                "=== CÓDIGO ANTERIOR ===\n"
                f"[index.html]\n{codigo_anterior.get('index_html', '')}\n\n"
                f"[style.css]\n{codigo_anterior.get('style_css', '')}\n\n"
                f"[script.js]\n{codigo_anterior.get('script_js', '')}\n"
            )
        else:
            prompt_usuario = (
                "Implemente a aplicação web completa atendendo à demanda principal e ao "
                "plano técnico do Coordenador.\n\n"
                f"=== DEMANDA PRINCIPAL ===\n{demanda}\n\n"
                f"=== PLANO DO COORDENADOR ===\n{plano_texto}\n"
            )

        resultado = self._chamar_gemini(
            nome_agente="Fullstack",
            instrucao_sistema=self.sys_fullstack,
            conteudo_usuario=prompt_usuario,
            schema=SCHEMA_FULLSTACK,
            temperatura=0.2,
        )

        arquivos = resultado["dados"].get("arquivos")
        if not isinstance(arquivos, dict):
            raise ErroExecucaoAgente("Campo 'arquivos' retornado pelo Fullstack não é um objeto.")
        for chave in ("index_html", "style_css", "script_js"):
            if chave not in arquivos or not str(arquivos[chave]).strip():
                raise ErroExecucaoAgente(
                    f"O agente Fullstack retornou o arquivo '{chave}' ausente ou vazio."
                )
            arquivos[chave] = self._remover_cercas_markdown(str(arquivos[chave]))

        return resultado

    def executar_qa_sec(
        self,
        demanda: str,
        plano: dict[str, Any] | str,
        arquivos_codigo: dict[str, str],
    ) -> dict[str, Any]:
        """Aciona o QA/Cibersegurança para auditoria estática dos arquivos gerados."""
        plano_texto = self._formatar_plano(plano)
        prompt_usuario = (
            "Realize a auditoria estática de qualidade, acessibilidade e cibersegurança "
            "sobre os três arquivos abaixo em comparação com a demanda e o plano.\n\n"
            f"=== DEMANDA PRINCIPAL ===\n{demanda}\n\n"
            f"=== PLANO DO COORDENADOR ===\n{plano_texto}\n\n"
            "=== CÓDIGO SUBMETIDO PARA AUDITORIA ESTÁTICA ===\n"
            f"[index.html]\n{arquivos_codigo.get('index_html', '')}\n\n"
            f"[style.css]\n{arquivos_codigo.get('style_css', '')}\n\n"
            f"[script.js]\n{arquivos_codigo.get('script_js', '')}\n"
        )

        resultado = self._chamar_gemini(
            nome_agente="QA_Ciberseguranca",
            instrucao_sistema=self.sys_qa_sec,
            conteudo_usuario=prompt_usuario,
            schema=SCHEMA_QA_SEC,
            temperatura=0.1,
        )

        dados = resultado["dados"]
        if not isinstance(dados.get("aprovado"), bool):
            raise ErroExecucaoAgente(
                "Campo 'aprovado' retornado pelo QA/Cibersegurança deve ser booleano."
            )
        if not isinstance(dados.get("achados"), list):
            raise ErroExecucaoAgente(
                "Campo 'achados' retornado pelo QA/Cibersegurança deve ser uma lista."
            )

        return resultado
