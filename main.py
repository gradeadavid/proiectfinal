"""
Application entry point.

This module provides a simple command-line
interface for interacting with the agent.
"""

import logging

from agent import Agent
from llm_client import LLMClient
from conversation_context import ConversationContext
from tools.tools import tools
from embedding_generator import generate_and_save_embeddings

logger = logging.getLogger(__name__)


def main():
    print("Initializing embeddings...")
    generate_and_save_embeddings()
    print()

    context = ConversationContext()

    llm_client = LLMClient()

    agent = Agent(llm_client, context, tools=tools)

    print("AI Assistant started. Type 'exit' to quit.")

    while True:
        try:
            user_input = input(
                "\nYou: "
            )
        except (EOFError, KeyboardInterrupt):
            print("\nLa revedere!")
            break

        if user_input.lower() == "exit":
            break

        try:
            # Track input tokens
            context.track_input_tokens(user_input)

            response = agent.process_message(user_input)

            # Track output tokens
            context.track_output_tokens(response)

            print(f"\nAI: {response}")

            # Display token and cost statistics
            stats = context.get_token_stats()
            costs = context.calculate_cost()

            print(f"\n--- Token Statistics ---")
            print(f"Input tokens:  {stats['input_tokens']}")
            print(f"Output tokens: {stats['output_tokens']}")
            print(f"Total tokens:  {stats['total_tokens']}")
            print(f"\n--- Cost Estimation ---")
            print(f"Input cost:    ${costs['input_cost']:.6f}")
            print(f"Output cost:   ${costs['output_cost']:.6f}")
            print(f"Total cost:    ${costs['total_cost']:.6f}")
            print(f"------------------------")
        except Exception:
            logger.exception("A aparut o problema la procesarea mesajului")
            print("\n[EROARE] A aparut o problema la procesarea mesajului.")
            print("Poti incerca din nou cu un alt mesaj.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    main()
