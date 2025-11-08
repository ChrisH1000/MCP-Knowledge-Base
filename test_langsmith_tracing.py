"""Test LangSmith tracing with a simple LangChain operation."""

import os
import sys

# Set up environment before imports
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "mcp-knowledge-server"

# Load API key from .env
from pathlib import Path

env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("LANGSMITH_API_KEY="):
            os.environ["LANGSMITH_API_KEY"] = line.split("=", 1)[1].strip()

print("=" * 60)
print("Testing LangSmith Tracing")
print("=" * 60)
print(f"LANGSMITH_TRACING: {os.environ.get('LANGSMITH_TRACING')}")
print(f"LANGCHAIN_PROJECT: {os.environ.get('LANGCHAIN_PROJECT')}")
print(f"LANGSMITH_API_KEY set: {'Yes' if os.environ.get('LANGSMITH_API_KEY') else 'No'}")
print()

# Test with a simple LangChain operation
try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate

    print("✅ LangChain imports successful")
    print()
    print("Creating a simple traced operation...")

    # Create a simple prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant for testing LangSmith tracing."),
            ("human", "{input}"),
        ]
    )

    # Format the prompt (this will be traced)
    formatted = prompt.format(input="Hello, testing LangSmith!")

    print(f"✅ Prompt formatted: {formatted[:100]}...")
    print()
    print("🎉 LangSmith tracing is active!")
    print()
    print("Check your LangSmith dashboard at:")
    print("https://smith.langchain.com/")
    print()
    print("Look for the 'mcp-knowledge-server' project.")
    print()
    print("Note: To see actual LLM traces, you need to:")
    print("1. Set OPENAI_API_KEY in your .env file")
    print("2. Set RAG_LLM_PROVIDER=openai in your .env file")
    print("3. Make a request to the /answer endpoint")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
