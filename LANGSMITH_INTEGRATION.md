# LangSmith Integration

This RAG server now includes [LangSmith](https://smith.langchain.com/) tracing for LLM observability and debugging.

## What is LangSmith?

LangSmith is a platform for debugging, testing, and monitoring LLM applications. It provides:
- **Tracing**: Track every step of your LLM calls
- **Debugging**: Inspect inputs, outputs, and intermediate steps
- **Monitoring**: Track performance and costs
- **Testing**: Run evaluations on your LLM applications

## Configuration

LangSmith is configured via environment variables in your `.env` file:

```bash
# Enable LangSmith tracing
LANGSMITH_TRACING=true

# Your LangSmith API key (get from https://smith.langchain.com/)
LANGSMITH_API_KEY=llsv2_pt_...

# Project name for organizing traces
LANGCHAIN_PROJECT=mcp-knowledge-server
```

## How It Works

When the RAG server starts:

1. The `Settings` class loads LangSmith configuration from `.env`
2. The `_setup_langsmith()` function sets the required environment variables:
   - `LANGSMITH_TRACING`: Enables tracing
   - `LANGSMITH_API_KEY`: Authenticates with LangSmith
   - `LANGCHAIN_PROJECT`: Organizes traces by project
3. Any LangChain/LangSmith-compatible LLM calls will be automatically traced

## Viewing Traces

1. Go to [https://smith.langchain.com/](https://smith.langchain.com/)
2. Sign in with your account
3. Navigate to your project (e.g., "mcp-knowledge-server")
4. View traces for all LLM interactions, including:
   - Query embeddings
   - Vector search results
   - LLM prompts and responses
   - Token usage and latency

## Testing

Run the test script to verify your configuration:

```bash
python3 test_langsmith.py
```

Expected output:
```
============================================================
LangSmith Configuration
============================================================
LANGSMITH_TRACING: true
LANGCHAIN_PROJECT: mcp-knowledge-server
LANGSMITH_API_KEY set: Yes

Environment Variables Set:
============================================================
os.environ['LANGSMITH_TRACING']: true
os.environ['LANGCHAIN_PROJECT']: mcp-knowledge-server
os.environ['LANGSMITH_API_KEY'] set: Yes

✅ LangSmith tracing is ENABLED
```

## Disabling LangSmith

To disable LangSmith tracing, set in your `.env`:

```bash
LANGSMITH_TRACING=false
```

Or remove/comment out the LangSmith environment variables.

## Security Notes

- The `LANGSMITH_API_KEY` is treated as a secret and redacted in config dumps
- Never commit your `.env` file with real API keys to version control
- The API key is automatically loaded into environment variables at startup

## Implementation Details

The LangSmith integration is implemented in:

- **`src/rag_server/core/config.py`**: Configuration and environment setup
  - `Settings` class includes LangSmith fields
  - `_setup_langsmith()` function sets environment variables
  - `get_settings()` initializes LangSmith on first call

- **`src/rag_server/server.py`**: Startup logging
  - Logs when LangSmith is enabled during app creation

This implementation follows the pattern from LangChain documentation, automatically setting environment variables that LangSmith-compatible libraries will detect.
