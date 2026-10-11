"""Entregable 2.1 — Refactorización a LCEL Asíncrono (course.pdf p.35-37).

Reemplaza la llamada manual al SDK del cliente unificado del Módulo 1
(projects/01-unified-async-llm-client) por una cadena LCEL:

    ChatPromptTemplate | ChatModel | StrOutputParser

Criterios de aceptación de la práctica (p.37):
    1. El flujo principal usa exclusivamente el operador `|` (LCEL).
    2. Ejecución asíncrona: `await chain.ainvoke(...)`.
    3. Salida en texto plano vía StrOutputParser (no el objeto de mensaje).
    4. Prompt con roles definidos (System/Human) vía ChatPromptTemplate.

Fuera de alcance a propósito: este script NO reproduce el retry con backoff,
la clasificación de errores ni el límite de concurrencia del cliente de M1.
La práctica pide enseñar la composición LCEL, no portar esa arquitectura
completa — queda anotado como limitación conocida, no como omisión.

    python main.py                  # usa el .env
    python main.py --provider openai
    python main.py --provider anthropic
"""

from __future__ import annotations

import argparse
import asyncio
import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

PREGUNTA = "¿Qué es la entropía?"


def construir_modelo(provider: str) -> Runnable:
    """Instancia el ChatModel de LangChain que reemplaza al SDK crudo de M1."""
    temperature = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.environ.get("LLM_MODEL") or "gpt-4o-mini",
            temperature=temperature,
            base_url=os.environ.get("OPENAI_BASE_URL") or None,
            api_key=os.environ["OPENAI_API_KEY"],
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.environ.get("LLM_MODEL") or "claude-sonnet-5",
            temperature=temperature,
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )

    raise ValueError(f"Proveedor no soportado: {provider!r} (usar openai|anthropic)")


def construir_cadena(provider: str) -> Runnable:
    """El flujo principal: Prompt -> Modelo -> Parser, compuesto con `|`."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres un divulgador científico. Responde en 3 frases."),
        ("human", "{pregunta}"),
    ])
    modelo = construir_modelo(provider)
    parser = StrOutputParser()

    return prompt | modelo | parser  # <- composición LCEL, criterio 1 y 4


async def main() -> None:
    parser_cli = argparse.ArgumentParser(description=__doc__)
    parser_cli.add_argument("--provider", choices=["openai", "anthropic"], default=None)
    args = parser_cli.parse_args()

    load_dotenv()
    provider = args.provider or os.environ.get("LLM_PROVIDER", "openai")

    chain = construir_cadena(provider)

    print(f"{'=' * 68}\nCadena LCEL — proveedor={provider}\n{'=' * 68}")
    print(f"Pregunta: {PREGUNTA}\n")

    # Criterio 2: ejecución asíncrona con ainvoke.
    respuesta = await chain.ainvoke({"pregunta": PREGUNTA})

    # Criterio 3: `respuesta` ya es un str (StrOutputParser lo garantiza),
    # no un BaseMessage con .content, .usage_metadata, etc.
    assert isinstance(respuesta, str)
    print(respuesta)


if __name__ == "__main__":
    asyncio.run(main())
