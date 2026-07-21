import json
from pathlib import Path
from utils import count_tokens
from config import (
    INPUT_TOKEN_PRICE_PER_MILLION, OUTPUT_TOKEN_PRICE_PER_MILLION
)


class ConversationContext:
    def __init__(self):
        self.knowledge_base_path = Path(__file__).parent / "knowledge"
        self.messages = [
            self.assemble_system_prompt()
        ]
        self.base_system_prompt = self.messages[0]["content"]
        self.input_tokens = 0
        self.output_tokens = 0
        self.summary = None

    def assemble_system_prompt(self):
        prompt_sections = []

        # 1. Load all prompts
        prompts_path = self.knowledge_base_path / "prompts"
        prompts_registry = self._load_registry(prompts_path / "registry.json")
        for doc_info in prompts_registry:
            content = self._load_document(prompts_path, doc_info["id"])
            if content:
                prompt_sections.append(f"# {doc_info['name']}\n{content}")

        # 2. Load facts marked with always_load: true
        facts_path = self.knowledge_base_path / "facts"
        facts_registry = self._load_registry(facts_path / "registry.json")
        for doc_info in facts_registry:
            if doc_info.get("always_load", False):
                content = self._load_document(facts_path, doc_info["id"])
                if content:
                    prompt_sections.append(f"# {doc_info['name']}\n{content}")

        # 3. Load procedures marked with always_load: true
        procedures_path = self.knowledge_base_path / "procedures"
        procedures_registry = self._load_registry(
            procedures_path / "registry.json")
        for doc_info in procedures_registry:
            if doc_info.get("always_load", False):
                content = self._load_document(procedures_path, doc_info["id"])
                if content:
                    prompt_sections.append(f"# {doc_info['name']}\n{content}")

        # Concatenate all sections
        final_prompt = "\n\n".join(prompt_sections)

        return {
            "role": "system",
            "content": final_prompt
        }

    def _load_registry(self, registry_path):
        """Load registry.json file and return the list of documents."""
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _load_document(self, directory_path, doc_id):
        """Load a markdown document by its ID."""
        doc_path = directory_path / f"{doc_id}.md"
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None

    def set_rag_context(self, rag_text):
        content = self.base_system_prompt
        if rag_text:
            content += "\n\n" + rag_text
        self.messages[0]["content"] = content

    def add_message(self, message):
        self.messages.append(message)

    def get_history(self):
        return self.messages

    def _conversation_start_index(self):
        return 2 if self.summary is not None else 1

    def get_turns(self):
        turns = []
        current_turn = []
        for message in self.messages[self._conversation_start_index():]:
            if message["role"] == "user":
                if current_turn:
                    turns.append(current_turn)
                current_turn = [message]
            else:
                current_turn.append(message)
        if current_turn:
            turns.append(current_turn)
        return turns

    def total_tokens(self):
        """Total token count across all messages currently in context."""
        return sum(count_tokens(m.get("content") or "") for m in self.messages)

    def pop_old_turns(self, keep_last_n):
        turns = self.get_turns()
        if len(turns) <= keep_last_n:
            return []

        old_turns = turns[:-keep_last_n] if keep_last_n > 0 else turns
        for turn in old_turns:
            for message in turn:
                self.messages.remove(message)
        return old_turns

    def set_summary(self, summary_text):
        """Store/update the rolling summary as a dedicated message right
        after the system prompt."""
        summary_message = {
            "role": "system",
            "content": f"Rezumat conversație anterioară:\n{summary_text}"
        }
        if self.summary is None:
            self.messages.insert(1, summary_message)
        else:
            self.messages[1] = summary_message
        self.summary = summary_text

    def track_input_tokens(self, text):
        tokens = count_tokens(text)
        self.input_tokens += tokens
        return tokens

    def track_output_tokens(self, text):
        tokens = count_tokens(text)
        self.output_tokens += tokens
        return tokens

    def get_token_stats(self):
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens
        }

    def calculate_cost(self):
        input_cost = (self.input_tokens / 1_000_000) * \
            INPUT_TOKEN_PRICE_PER_MILLION
        output_cost = (self.output_tokens / 1_000_000) * \
            OUTPUT_TOKEN_PRICE_PER_MILLION
        total_cost = input_cost + output_cost

        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6)
        }
