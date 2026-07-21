from dotenv import load_dotenv
import os
load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = "gpt-5-mini"

#la SUMMARY_MODEL_NAME doream sa folosesc un alt model mai mic,dar nu este mapat in Azure si in folosesc pe acelasi 
SUMMARY_MODEL_NAME = "gpt-5-mini"
SYSTEM_PROMPT = ""
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

EMBEDDINGS_MODEL = "qwen3-embedding:8b"
EMBEDDINGS_ENDPOINT = os.getenv(
    "EMBEDDINGS_ENDPOINT",
    "http://localhost:11434/api/embeddings")

INPUT_TOKEN_PRICE_PER_MILLION = 2.0
OUTPUT_TOKEN_PRICE_PER_MILLION = 10.0


RAG_TOP_K = 3
RAG_MIN_SIMILARITY = 0.4

MAX_CONTEXT_TOKENS = 4000
KEEP_LAST_TURNS = 3

MAX_TOOL_ROUNDS = 5
