# Startup Mentor Agent

Agent conversațional (Python) pentru sprijinirea deciziilor de produs și business,
cu acces la o bază de cunoștințe proprie (RAG) și la tool-uri de analiză. Expune
două interfețe care rulează peste același `Agent`: un CLI (`main.py`) și o
aplicație web Flask (`webapp/app.py`).

## Funcționalități

- **CLI** (`main.py`) — conversație în terminal; după fiecare răspuns afișează
  statistici de tokeni și o estimare de cost.
- **Web app** (`webapp/app.py`) — interfață tip ChatGPT, cu autentificare doar pe
  bază de email (fără parolă). Fiecare utilizator are propriile conversații,
  salvate ca fișiere JSON în `webapp/data/`, cu opțiuni de redenumire, ștergere,
  export și import.
- **RAG / Embeddings** (`knowledge/`, `document_chunker.py`,
  `embedding_generator.py`, `embeddings_client.py`) — documentele din
  `knowledge/` sunt împărțite în chunk-uri, transformate în embeddings și
  cache-uite incremental în `embeddings.json` (se regenerează doar ce s-a
  schimbat).
- **Tool-uri** (`tools/`) — descoperite automat și puse la dispoziția modelului:


## Arhitectură (schematic)

- `agent.py` — orchestrare: caută context relevant prin RAG, gestionează
  compresia conversației (sumarizare când se depășește `MAX_CONTEXT_TOKENS`),
  alege modelul și rulează buclă de tool-calling.
- `llm_client.py` — client OpenAI-compatible (librăria `openai`), configurat
  prin `AZURE_ENDPOINT`/`API_KEY`.
- `conversation_context.py` — istoric conversație, sumarizare, tracking
  tokeni/cost.
- `document_chunker.py`, `embedding_generator.py`, `embeddings_client.py` —
  chunk-uire, generare și căutare semantică pe embeddings.
- `tools/` — tool-uri Python apelabile de agent, plus infrastructura de
  descoperire (`tool.py`, `tools.py`).
- `webapp/` — aplicația Flask: `app.py` (rute), `user_store.py` (persistență
  conversații per utilizator în `webapp/data/`), `templates/`, `static/`.

## Instalare

```bash
pip install -r requirements.txt
```

### Prerequisite: Ollama (pentru embeddings)

Generarea embeddings-urilor (RAG) folosește implicit un server **Ollama** local,
prin `EMBEDDINGS_ENDPOINT` (`http://localhost:11434/api/embeddings`) și modelul
`EMBEDDINGS_MODEL` (`qwen3-embedding:8b`, hardcodat în `config.py`). Înainte de
prima rulare:

1. Instalează Ollama de pe [ollama.com](https://ollama.com).
2. Descarcă modelul de embeddings:
   ```bash
   ollama pull qwen3-embedding:8b
   ```
3. Asigură-te că Ollama rulează (implicit ascultă pe portul `11434`).

Fără acești pași, `main.py`/`webapp/app.py` vor eșua la generarea embeddings-urilor
cu o eroare de conexiune sau model inexistent.

## Configurare variabile de mediu

Creează un fișier `.env` în rădăcina proiectului (nu îl comite în Git — e deja
în `.gitignore`). Variabile citite din `config.py`:

- `AZURE_ENDPOINT` — endpoint OpenAI-compatible pentru modelul de chat 
- `API_KEY` — cheia API pentru acel endpoint.
- `EMBEDDINGS_ENDPOINT` — endpoint pentru generarea embeddings-urilor;
  implicit `http://localhost:11434/api/embeddings` (compatibil Ollama).
- `FLASK_SECRET_KEY` — cheia de sesiune Flask, folosită de `webapp/app.py`
  (dacă lipsește, se generează una aleatoare la fiecare pornire, ceea ce
  invalidează sesiunile existente la restart).

Modelele folosite (`MODEL_NAME`, `SUMMARY_MODEL_NAME`, `EMBEDDINGS_MODEL`) și
prețurile per milion de tokeni sunt hardcodate în `config.py`.

## Rulare

CLI:

```bash
python main.py
```

Web app:

```bash
python webapp/app.py
```

La pornire, ambele interfețe (re)generează embeddings pentru documentele din
`knowledge/` și salvează rezultatul în `embeddings.json`.

## Teste

```bash
pytest
```

Acoperire curentă: `tests/test_embeddings_client.py`.

## Note

- `embeddings.json` și `webapp/data/` sunt cache/date locale, excluse din Git
  (vezi `.gitignore`).
- Nivelul de log implicit este `DEBUG` (configurat în `main.py` /
  `webapp/app.py`)