"""Test script to verify LangSmith integration."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from rag_server.core.config import get_settings


def main():
    settings = get_settings()

    print("=" * 60)
    print("LangSmith Configuration")
    print("=" * 60)
    print(f"LANGSMITH_TRACING: {settings.LANGSMITH_TRACING}")
    print(f"LANGCHAIN_PROJECT: {settings.LANGCHAIN_PROJECT}")
    print(f"LANGSMITH_API_KEY set: {'Yes' if settings.LANGSMITH_API_KEY else 'No'}")
    print()

    print("Environment Variables Set:")
    print("=" * 60)
    print(f"os.environ['LANGSMITH_TRACING']: {os.environ.get('LANGSMITH_TRACING', 'Not set')}")
    print(f"os.environ['LANGCHAIN_PROJECT']: {os.environ.get('LANGCHAIN_PROJECT', 'Not set')}")
    print(
        f"os.environ['LANGSMITH_API_KEY'] set: {'Yes' if os.environ.get('LANGSMITH_API_KEY') else 'No'}"
    )
    print()

    if settings.LANGSMITH_TRACING.lower() == "true":
        print("✅ LangSmith tracing is ENABLED")
    else:
        print("❌ LangSmith tracing is DISABLED")


if __name__ == "__main__":
    main()
