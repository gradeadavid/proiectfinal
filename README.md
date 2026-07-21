# Startup Mentor Agent

A conversational agent (Python) for supporting product and business decisions,
with access to its own knowledge base (RAG) and analysis tools. It exposes
two interfaces running on top of the same `Agent`: a CLI (`main.py`) and a
Flask web app (`webapp/app.py`).

## Features

- **CLI** (`main.py`) — terminal conversation; after each response it shows
  token statistics and a cost estimate.
- **Web app** (`webapp/app.py`) — ChatGPT-style interface, with email-only
  authentication (no password). Each user has their own conversations,
  saved as JSON files in `webapp/data/`, with options to rename, delete,
  export, and import.
- **RAG / Embeddings** (`knowledge/`, `document_chunker.py`,
  `embedding_generator.py`, `embeddings_client.py`) — documents in
  `knowledge/` are split into chunks, converted into embeddings, and
  cached incrementally in `embeddings.json` (only changed content is
  regenerated).
- **Tools** (`tools/`) — automatically discovered and made available to the model:


## Architecture (overview)

- `agent.py` — orchestration: retrieves relevant context via RAG, handles
  conversation compression (summarization when `MAX_CONTEXT_TOKENS` is
  exceeded), selects the model, and runs the tool-calling loop.
- `llm_client.py` — OpenAI-compatible client (`openai` library), configured
  via `AZURE_ENDPOINT`/`API_KEY`.
- `conversation_context.py` — conversation history, summarization, token/cost
  tracking.
- `document_chunker.py`, `embedding_generator.py`, `embeddings_client.py` —
  chunking, generation, and semantic search over embeddings.
- `tools/` — Python tools callable by the agent, plus the discovery
  infrastructure (`tool.py`, `tools.py`).
- `webapp/` — the Flask application: `app.py` (routes), `user_store.py`
  (per-user conversation persistence in `webapp/data/`), `templates/`,
  `static/`.

## Installation

1. Create and activate a Python virtual environment in the project directory:

```bash
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

CMD:

```batch
.\.venv\Scripts\activate.bat
```

If PowerShell blocks scripts due to the execution policy, use CMD or run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

### Prerequisite: Ollama (for embeddings)

Embedding generation (RAG) uses a local **Ollama** server by default,
via `EMBEDDINGS_ENDPOINT` (`http://localhost:11434/api/embeddings`) and the
`EMBEDDINGS_MODEL` model (`qwen3-embedding:8b`, hardcoded in `config.py`).
Before the first run:

1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull the embeddings model:
   ```bash
   ollama pull qwen3-embedding:8b
   ```
3. Make sure Ollama is running (it listens on port `11434` by default).

Without these steps, `main.py`/`webapp/app.py` will fail to generate
embeddings with a connection error or a "model not found" error.

## Environment variable configuration

Create a `.env` file in the project root (do not commit it to Git — it is
already in `.gitignore`). Variables read from `config.py`:

- `AZURE_ENDPOINT` — OpenAI-compatible endpoint for the chat model.
- `API_KEY` — the API key for that endpoint.
- `EMBEDDINGS_ENDPOINT` — endpoint for generating embeddings;
  defaults to `http://localhost:11434/api/embeddings` (Ollama-compatible).
- `FLASK_SECRET_KEY` — Flask session key, used by `webapp/app.py`
  (if missing, a random one is generated on every startup, which
  invalidates existing sessions on restart).

The models used (`MODEL_NAME`, `SUMMARY_MODEL_NAME`, `EMBEDDINGS_MODEL`) and
the prices per million tokens are hardcoded in `config.py`.

## Running

CLI:

```bash
python main.py
```

Web app:

```bash
python webapp/app.py
```

On startup, both interfaces (re)generate embeddings for the documents in
`knowledge/` and save the result to `embeddings.json`.

## Tests

```bash
pytest
```

Current coverage: `tests/test_embeddings_client.py`.

## Notes

- `embeddings.json` and `webapp/data/` are local cache/data, excluded from
  Git (see `.gitignore`).
- The default log level is `DEBUG` (configured in `main.py` /
  `webapp/app.py`).
