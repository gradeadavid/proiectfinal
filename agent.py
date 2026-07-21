import json
import logging
from concurrent.futures import ThreadPoolExecutor
from embeddings_client import EmbeddingsClient
from config import (
    RAG_TOP_K, RAG_MIN_SIMILARITY, MAX_CONTEXT_TOKENS, KEEP_LAST_TURNS,
    MAX_TOOL_ROUNDS, MODEL_NAME, SUMMARY_MODEL_NAME
)

logger = logging.getLogger(__name__)

NO_RESPONSE_FALLBACK = (
    "Nu am putut genera un răspuns pentru asta acum. "
    "Poți reformula întrebarea sau încerca din nou?"
)

SUMMARIZATION_SYSTEM_PROMPT = (
    "Rezumă concis conversația de mai jos dintre un founder și un mentor "
    "de startup. Păstrează cifre, decizii și fapte concrete menționate. "
    "Maxim 150 de cuvinte."
)

SIMPLE_MESSAGE_MAX_WORDS = 8

SUBSTANTIVE_KEYWORDS = (
    "piata", "piață", "competitor", "concuren", "finant", "buget", "runway",
    "swot", "strateg", "produs", "marketing", "investi", "cash", "venit",
    "cost", "vanz", "vânz", "client", "afacer", "startup", "lansare",
    "pret", "preț"
)


class Agent:
    def __init__(self, llm_client, context, tools=None):
        self.llm_client = llm_client
        self.context = context
        self.tools = {tool.name: tool for tool in tools} if tools else {}
        self.embeddings_client = EmbeddingsClient()

    def _execute_tool_call(self, tc):
        tool_name = tc["function"]["name"]
        arguments = tc["function"]["arguments"]
        tool_id = tc["id"]

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        logger.info(
            "Executing tool call: %s with arguments: %s",
            tool_name, arguments
        )

        tool = self.tools.get(tool_name)
        if tool:
            try:
                result = tool.callback(**arguments)
            except Exception as e:
                logger.exception("Tool '%s' failed", tool_name)
                result = f"Tool '{tool_name}' failed with an error: {e}"
        else:
            result = f"Tool '{tool_name}' not found"

        logger.info("Tool '%s' result: %s", tool_name, result)

        return {
            "role": "tool",
            "tool_call_id": tool_id,
            "content": str(result)
        }

    def _handle_tool_calls(self, tool_calls):
        if len(tool_calls) == 1:
            return [self._execute_tool_call(tool_calls[0])]

        with ThreadPoolExecutor(max_workers=len(tool_calls)) as executor:
            return list(executor.map(self._execute_tool_call, tool_calls))

    def _enhance_system_prompt_with_search_results(self, user_message):
        try:
            search_results = self.embeddings_client.semantic_search(
                user_question=user_message,
                top_k=RAG_TOP_K,
                min_similarity=RAG_MIN_SIMILARITY
            )

            if search_results:
                relevant_context = (
                    "## Relevant Information from Knowledge Base:\n\n"
                )
                for i, result in enumerate(search_results, 1):
                    relevant_context += (
                        f"**[{result['document_id']} - "
                        f"Chunk {result['chunk_index']}] "
                        f"(Similarity: {result['similarity']:.2f})**\n"
                    )
                    relevant_context += f"{result['content']}\n\n"

                self.context.set_rag_context(relevant_context)

                return True
            logger.info(
                "No relevant knowledge base results found for this question.")
            self.context.set_rag_context(None)
            return False
        except Exception as e:
            logger.warning(
                "Semantic search unavailable, proceeding without RAG "
                "context: %s",
                e, exc_info=True
            )
            return False

    def _flatten_turns(self, turns):
        lines = []
        for turn in turns:
            for message in turn:
                role = message["role"]
                content = message.get("content")

                if role == "user":
                    lines.append(f"Founder: {content}")
                elif role == "assistant":
                    if content:
                        lines.append(f"Mentor: {content}")
                    if message.get("tool_calls"):
                        tool_names = ", ".join(
                            tc["function"]["name"]
                            for tc in message["tool_calls"]
                        )
                        lines.append(
                            "[Mentor a folosit tool-ul/tool-urile: "
                            f"{tool_names}]"
                        )
                elif role == "tool":
                    lines.append(f"[Rezultat tool: {content}]")
        return "\n".join(lines)

    def _compress_context_if_needed(self):

        tokens_before = self.context.total_tokens()
        if tokens_before <= MAX_CONTEXT_TOKENS:
            return

        old_turns = self.context.pop_old_turns(keep_last_n=KEEP_LAST_TURNS)
        if not old_turns:
            return

        logger.info(
            "Total tokens (%d) exceeded MAX_CONTEXT_TOKENS (%d); "
            "summarizing %d old turn(s).",
            tokens_before, MAX_CONTEXT_TOKENS, len(old_turns)
        )

        flattened = self._flatten_turns(old_turns)
        previous_summary = self.context.summary or "(niciun rezumat anterior)"

        logger.debug("Previous summary fed in:\n%s", previous_summary)
        logger.debug("Raw transcript being summarized:\n%s", flattened)

        summarization_messages = [
            {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
            {"role": "user", "content": (
                previous_summary + "\n\n" + flattened).strip()}
        ]

        response = self.llm_client.generate_response(
            summarization_messages, model=SUMMARY_MODEL_NAME)
        new_summary = response["message"].get(
            "content") or self.context.summary or "(fara continut anterior)"

        self.context.set_summary(new_summary)

        tokens_after = self.context.total_tokens()
        logger.debug("New summary:\n%s", new_summary)
        logger.info(
            "Tokens: %d -> %d (%d turn(s) compressed).",
            tokens_before, tokens_after, len(old_turns)
        )

    def _select_model(self, user_message):
        text = user_message.lower()
        word_count = len(user_message.split())

        looks_substantive = (
            word_count > SIMPLE_MESSAGE_MAX_WORDS
            or any(keyword in text for keyword in SUBSTANTIVE_KEYWORDS)
        )
        return MODEL_NAME if looks_substantive else SUMMARY_MODEL_NAME

    def process_message(self, user_message):
        logger.info("Received user message: %s", user_message)

        self._enhance_system_prompt_with_search_results(user_message)

        self.context.add_message({
            "role": "user",
            "content": user_message
        })

        self._compress_context_if_needed()

        selected_model = self._select_model(user_message)
        logger.debug("Using model '%s' for this message.", selected_model)

        message = None
        for round_num in range(MAX_TOOL_ROUNDS):
            response = self.llm_client.generate_response(
                self.context.get_history(),
                tools=list(self.tools.values()),
                model=selected_model
            )
            message = response["message"]
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                break

            logger.debug(
                "Model decided to use %d tool(s) (round %d/%d).",
                len(tool_calls), round_num + 1, MAX_TOOL_ROUNDS
            )
            self.context.add_message(message)

            tool_results = self._handle_tool_calls(tool_calls)
            for result in tool_results:
                self.context.add_message(result)
        else:
            logger.warning(
                "Reached MAX_TOOL_ROUNDS (%d) without a final answer. "
                "Forcing a response without tools.",
                MAX_TOOL_ROUNDS
            )
            response = self.llm_client.generate_response(
                self.context.get_history(), model=selected_model)
            message = response["message"]

        content = message.get("content")
        if not content or not content.strip():
            logger.warning("Model returned an empty response.")
            content = NO_RESPONSE_FALLBACK
            message["content"] = content

        logger.info("Generated response: %s", content)

        self.context.add_message(message)
        return content
