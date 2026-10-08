"""
Model Router Python SDK Quickstart Example.
Demonstrates chat completions, streaming, and dry-run routing.
"""

import os
import sys

# Add sdk/python to path for local execution without pip install
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sdk", "python")))

from modelrouter import ModelRouter, AsyncModelRouter


def sync_example():
    print("\n--- 1. Synchronous Chat Completion ---")
    client = ModelRouter(base_url="http://localhost:8000", policy="balanced")
    
    # 1. Routing dry-run
    decision = client.route("Write an asynchronous Python web scraper using httpx")
    print(f"[Route Decision] Model: {decision.selected_model_name} (Tier: {decision.tier})")
    print(f"[Why] {', '.join(decision.reasons)}")

    # 2. Complete request
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Explain binary search trees in one sentence."}
        ]
    )
    print(f"[Response from {response.model}] {response.choices[0].message.content}")
    print(f"[Tokens] Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}")


def stream_example():
    print("\n--- 2. Real-Time Streaming ---")
    client = ModelRouter(base_url="http://localhost:8000")
    stream = client.chat.completions.create(
        prompt="Write a Python hello world script",
        stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()


if __name__ == "__main__":
    sync_example()
    stream_example()
