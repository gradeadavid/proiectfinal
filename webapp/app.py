"""Web interface for the Startup Mentor Agent.

Users identify themselves with just an email (no password) and get a
ChatGPT-style sidebar of their own separate conversations, each backed by
the same Agent used by the CLI (main.py). Run with: python webapp/app.py
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# These imports must come after the sys.path.insert above, since several
# of them (user_store, agent, llm_client, ...) live outside webapp/ and
# are only importable once the parent directory is on sys.path.
from flask import (  # noqa: E402
    Flask, Response, render_template, request, redirect, url_for, session
)

import user_store  # noqa: E402
from agent import Agent  # noqa: E402
from llm_client import LLMClient  # noqa: E402
from conversation_context import ConversationContext  # noqa: E402
from tools.tools import tools  # noqa: E402
from embedding_generator import generate_and_save_embeddings  # noqa: E402
from utils import count_tokens  # noqa: E402

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

_llm_client = LLMClient()
_agents: dict[tuple[str, str], Agent] = {}


def get_or_create_agent(email: str, conversation_id: str) -> Agent:
    """Return the in-memory Agent for this (email, conversation), creating
    one and replaying that conversation's persisted messages into its
    context on first use."""
    key = (user_store.normalize_email(email), conversation_id)
    if key not in _agents:
        context = ConversationContext()
        agent = Agent(_llm_client, context, tools=tools)
        for message in user_store.load_conversation_messages(
                email, conversation_id):
            context.add_message({
                "role": message["role"],
                "content": message["content"]
            })
        _agents[key] = agent
    return _agents[key]


def _current_email():
    return session.get("email")


def _render_chat(email, active_id, messages):
    conversations = user_store.load_conversations(email)
    enriched_messages = [
        {**message, "tokens": count_tokens(message["content"])}
        for message in messages
    ]
    return render_template(
        "chat.html",
        email=email,
        conversations=conversations,
        active_id=active_id,
        messages=enriched_messages
    )


@app.route("/")
def index():
    if _current_email():
        return redirect(url_for("chat_root"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)

    email = request.form.get("email", "")
    if not user_store.is_valid_email(email):
        return render_template(
            "login.html", error="Introdu o adresa de email valida.")

    session["email"] = user_store.normalize_email(email)
    return redirect(url_for("chat_root"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/chat")
def chat_root():
    email = _current_email()
    if not email:
        return redirect(url_for("login"))

    conversations = user_store.load_conversations(email)
    if conversations:
        return redirect(
            url_for("chat_get", conversation_id=conversations[0]["id"]))
    return redirect(url_for("new_chat"))


@app.route("/chat/new", methods=["GET"])
def new_chat():
    email = _current_email()
    if not email:
        return redirect(url_for("login"))
    return _render_chat(email, active_id=None, messages=[])


@app.route("/chat/new", methods=["POST"])
def new_chat_post():
    email = _current_email()
    if not email:
        return redirect(url_for("login"))

    user_message = request.form.get("message", "").strip()
    if not user_message:
        return redirect(url_for("new_chat"))

    conversation_id = user_store.create_conversation(
        email, first_message=user_message)
    agent = get_or_create_agent(email, conversation_id)
    start_time = time.monotonic()
    try:
        response = agent.process_message(user_message)
    except Exception as e:
        response = f"A aparut o eroare neasteptata: {e}"
    response_time = round(time.monotonic() - start_time, 2)

    user_store.append_messages(email, conversation_id, [
        {"role": "user", "content": user_message},
        {
            "role": "assistant",
            "content": response,
            "response_time": response_time
        }
    ])

    return redirect(url_for("chat_get", conversation_id=conversation_id))


@app.route("/chat/<conversation_id>", methods=["GET"])
def chat_get(conversation_id):
    email = _current_email()
    if not email:
        return redirect(url_for("login"))

    messages = user_store.load_conversation_messages(email, conversation_id)
    return _render_chat(email, active_id=conversation_id, messages=messages)


@app.route("/chat/<conversation_id>", methods=["POST"])
def chat_post(conversation_id):
    email = _current_email()
    if not email:
        return redirect(url_for("login"))

    user_message = request.form.get("message", "").strip()
    if not user_message:
        return redirect(url_for("chat_get", conversation_id=conversation_id))

    agent = get_or_create_agent(email, conversation_id)
    start_time = time.monotonic()
    try:
        response = agent.process_message(user_message)
    except Exception as e:
        response = f"A aparut o eroare neasteptata: {e}"
    response_time = round(time.monotonic() - start_time, 2)

    user_store.append_messages(email, conversation_id, [
        {"role": "user", "content": user_message},
        {
            "role": "assistant",
            "content": response,
            "response_time": response_time
        }
    ])

    return redirect(url_for("chat_get", conversation_id=conversation_id))


@app.route("/chat/<conversation_id>/delete", methods=["POST"])
def delete_chat(conversation_id):
    email = _current_email()
    if not email:
        return redirect(url_for("login"))

    user_store.delete_conversation(email, conversation_id)
    _agents.pop((user_store.normalize_email(email), conversation_id), None)

    return redirect(url_for("chat_root"))


@app.route("/chat/<conversation_id>/rename", methods=["POST"])
def rename_chat(conversation_id):
    email = _current_email()
    if not email:
        return redirect(url_for("login"))

    new_title = request.form.get("title", "")
    user_store.rename_conversation(email, conversation_id, new_title)

    return redirect(url_for("chat_get", conversation_id=conversation_id))


@app.route("/chat/<conversation_id>/export")
def export_chat(conversation_id):
    email = _current_email()
    if not email:
        return redirect(url_for("login"))

    conversation = user_store.get_conversation(email, conversation_id)
    if not conversation:
        return redirect(url_for("chat_root"))

    payload = json.dumps(conversation, indent=2, ensure_ascii=False)
    return Response(
        payload,
        mimetype="application/json",
        headers={
            "Content-Disposition": (
                f"attachment; filename=conversatie_{conversation_id}.json"
            )
        }
    )


@app.route("/chat/import", methods=["POST"])
def import_chat():
    email = _current_email()
    if not email:
        return redirect(url_for("login"))

    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return redirect(url_for("chat_root"))

    try:
        data = json.load(uploaded.stream)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return redirect(url_for("chat_root"))

    if not isinstance(data, dict):
        return redirect(url_for("chat_root"))

    messages = [
        {"role": m["role"], "content": m["content"],
            "timestamp": m.get("timestamp", "")}
        for m in data.get("messages", [])
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
    ]

    conversation_id = user_store.import_conversation(
        email,
        title=data.get("title", "Conversatie importata"),
        messages=messages
    )

    return redirect(url_for("chat_get", conversation_id=conversation_id))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    print("Initializing embeddings...")
    generate_and_save_embeddings()
    print()
    app.run(debug=True)
