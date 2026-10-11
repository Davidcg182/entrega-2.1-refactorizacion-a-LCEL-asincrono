# LCEL Async Refactor

Refactorización del cliente de LLM asíncrono (SDK crudo, Módulo 1) a una cadena declarativa de
**LCEL** (LangChain Expression Language).

**Entregable, unidad 2.1 · Módulo 2 — Coderhouse AI Engineering.**

---

## El problema

El cliente del Módulo 1 (`unified-async-llm-client`) llama al SDK del proveedor de forma
imperativa: formatear el prompt, invocar al modelo y parsear la respuesta son tres pasos que el
código orquesta a mano. Funciona, pero cada paso nuevo (streaming, un paso de validación, correr
dos sub-tareas en paralelo) exige tocar ese código de orquestación.

LCEL propone una alternativa: cada paso es un **Runnable** con interfaz uniforme
(`invoke`/`ainvoke`/`batch`/`stream`), y se compone con el operador `|` en vez de código de
pegamento escrito a mano.

## Qué hace este repo

`main.py` define y ejecuta una cadena LCEL asíncrona concreta:

```python
chain = prompt | modelo | parser
respuesta = await chain.ainvoke({"pregunta": "..."})
```

- **Prompt:** `ChatPromptTemplate.from_messages` con roles `system`/`human`.
- **Modelo:** `ChatOpenAI` o `ChatAnthropic` (según `LLM_PROVIDER`), en reemplazo del SDK crudo.
- **Parser:** `StrOutputParser`, para que el flujo entregue texto plano en vez del objeto de
  mensaje (`BaseMessage`) del modelo.

## Instalación y ejecución

Requiere **Python 3.12+**.

```bash
python3 -m venv .venv && source .venv/bin/activate   # o: uv venv --python 3.12 .venv
pip install -r requirements.txt                      # o: uv pip install -r requirements.txt
cp .env.example .env   # completar con tu proveedor y clave
python main.py
python main.py --provider anthropic
```

## Criterios de aceptación cubiertos

| Criterio | Cómo se cumple |
| --- | --- |
| Flujo principal exclusivamente con LCEL (`\|`) | `construir_cadena()`: `prompt \| modelo \| parser`, sin pasos imperativos intermedios |
| Ejecución asíncrona | `await chain.ainvoke({...})` en `main()` |
| Salida en texto plano | `StrOutputParser` + `assert isinstance(respuesta, str)` |
| Prompt con roles definidos | `ChatPromptTemplate.from_messages([("system", ...), ("human", ...)])` |

## Fuera de alcance (a propósito)

Esta práctica refactoriza **la composición del flujo**, no la arquitectura de resiliencia del
Módulo 1. No se reproducen acá:

- Retry con backoff + jitter y clasificación de errores (`BaseLLMClient` del M1).
- Límite de concurrencia (`asyncio.Semaphore`).
- Streaming, validación de configuración al arrancar, `SecretStr` para las claves.

Eso vive en `projects/01-unified-async-llm-client`. Esta práctica es puntual: demostrar la
composición LCEL reemplazando la llamada manual al SDK.
