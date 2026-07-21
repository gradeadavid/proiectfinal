"""
LLM integration layer.

This module is responsible for all communication
with the language model.
"""

import logging

from openai import OpenAI

from config import (
    MODEL_NAME,
    AZURE_ENDPOINT,
    API_KEY
)

from tools.tool import Tool

logger = logging.getLogger(__name__)

FALLBACK_ERROR_MESSAGE = (
    "Îmi pare rău, am întâmpinat o problemă tehnică și nu am putut "
    "genera un răspuns. Poți încerca din nou?"
)


class LLMClient:

    def __init__(self):
        self.client = OpenAI(
            base_url=AZURE_ENDPOINT,
            api_key=API_KEY
        )

    def _tool_to_dict(self, tool: Tool):
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        }

    def generate_response(self, messages, tools=None, model=None):

        kwargs = {
            "model": model or MODEL_NAME,
            "messages": messages
        }

        if tools:
            kwargs["tools"] = [
                self._tool_to_dict(tool)
                for tool in tools
            ]

        try:
            response = self.client.chat.completions.create(
                **kwargs
            )
        except Exception:
            logger.exception("LLM request failed")
            return {
                "message": {
                    "role": "assistant",
                    "content": FALLBACK_ERROR_MESSAGE
                }
            }

        message = response.choices[0].message

        result = {
            "message": {
                "role": "assistant",
                "content": message.content
            }
        }

        if getattr(message, "tool_calls", None):

            result["message"]["tool_calls"] = []

            for tc in message.tool_calls:

                result["message"]["tool_calls"].append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

        return result
