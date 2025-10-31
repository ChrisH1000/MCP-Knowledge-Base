# LangSmith Tracing - Complete Guide

## The Issue You Encountered

**Q: Why isn't my LangSmith project appearing in the dashboard?**

**A: LangSmith only traces LangChain operations.** Simply setting environment variables isn't enough - you need to use LangChain's LLM wrappers.

### What Was Wrong

Your original code used:
- **Direct OpenAI SDK** (`from openai import OpenAI`)
- **Direct HTTP calls** to Ollama (`httpx.AsyncClient`)

These don't send traces to LangSmith because they're not LangChain operations.

### What We Fixed

We updated your LLM clients to use LangChain:
- **OpenAI**: Now uses `langchain_openai.ChatOpenAI`
- **Ollama**: Now uses `langchain_community.llms.Ollama`

## How LangSmith Tracing Works

```
LangSmith Tracing Flow:
┌─────────────────────────────────────────────────┐
│ 1. Environment Variables Set (from .env)       │
│    • LANGSMITH_TRACING=true                     │
│    • LANGSMITH_API_KEY=lsv2_pt_...             │
│    • LANGCHAIN_PROJECT=mcp-knowledge-server     │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 2. LangChain Detects These Variables           │
│    • Automatically enables tracing              │
│    • Configures project name                    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 3. LangChain Operations Run                     │
│    • ChatOpenAI.invoke()                        │
│    • Ollama.ainvoke()                           │
│    • Prompts, chains, agents, etc.              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 4. Traces Sent to LangSmith                     │
│    • Inputs, outputs, metadata                  │
│    • Token usage, latency                       │
│    • Error traces if any                        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 5. View in Dashboard                            │
│    https://smith.langchain.com/                 │
│    → Your Project: mcp-knowledge-server         │
└─────────────────────────────────────────────────┘
```

## What Changed in the Code

### Before (No Tracing)

**src/rag_server/llm/openai_client.py**
```python
from openai import OpenAI

self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
response = self.client.chat.completions.create(...)
# ❌ This does NOT trace to LangSmith
```

### After (With Tracing)

**src/rag_server/llm/openai_client.py**
```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

self.client = ChatOpenAI(model=settings.LLM_MODEL, ...)
response = self.client.invoke([HumanMessage(content=prompt)])
# ✅ This DOES trace to LangSmith automatically
```

## How to See Traces in LangSmith

### Step 1: Configure Your .env

```bash
# Enable LangSmith
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...  # Your API key
LANGCHAIN_PROJECT=mcp-knowledge-server

# Enable OpenAI (to actually make LLM calls)
RAG_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...  # Your OpenAI API key
```

### Step 2: Start the Server

```bash
make run
# or
python3 src/main.py
```

You should see in the logs:
```
langsmith_enabled project=mcp-knowledge-server tracing=True
```

### Step 3: Make an LLM Request

```bash
curl -X POST http://localhost:8000/answer \
  -H "x-api-key: test-api-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "How does this codebase work?",
    "top_k": 5
  }'
```

### Step 4: Check LangSmith Dashboard

1. Go to https://smith.langchain.com/
2. Sign in with your account
3. Navigate to **Projects** → **mcp-knowledge-server**
4. You should see:
   - Run traces for each `/answer` request
   - Input prompts with retrieved context
   - LLM responses
   - Token counts and latency
   - Any errors that occurred

## What Gets Traced

When you use the `/answer` endpoint with LangSmith enabled:

### Automatic Traces Include:

1. **LLM Call**
   - Model used (e.g., `gpt-4o-mini`)
   - Full prompt sent to the model
   - Response generated
   - Token usage (prompt, completion, total)
   - Latency (time to generate)

2. **Metadata**
   - Timestamp
   - Status (success/error)
   - Model parameters (temperature, max_tokens)
   - Project name

3. **Error Traces** (if any)
   - Exception details
   - Stack traces
   - Failed inputs

### What's NOT Traced (Yet)

The following are NOT automatically traced because they don't use LangChain:
- Vector store searches (FAISS)
- Keyword searches (BM25)
- File ingestion

To trace these, you'd need to add custom LangSmith instrumentation.

## Testing LangSmith Integration

### Test 1: Verify Configuration

```bash
python3 test_langsmith.py
```

Expected output:
```
✅ LangSmith tracing is ENABLED
```

### Test 2: Test LangChain Operations

```bash
python3 test_langsmith_tracing.py
```

Expected output:
```
🎉 LangSmith tracing is active!
```

### Test 3: Make an Actual Request

```bash
# Start server in one terminal
make run

# In another terminal, make a request
make query
```

Then check https://smith.langchain.com/ for the trace.

## Troubleshooting

### Project Not Appearing in LangSmith?

**Check these:**

1. ✅ Environment variables are set correctly
   ```bash
   python3 test_langsmith.py
   ```

2. ✅ You're using LangChain, not direct SDK calls
   ```python
   # ❌ Won't trace
   from openai import OpenAI
   
   # ✅ Will trace
   from langchain_openai import ChatOpenAI
   ```

3. ✅ You've made at least one LLM request
   - Projects only appear after the first trace is sent
   - Use `/answer` endpoint, not `/query` (which doesn't use LLM)

4. ✅ Your API key is valid
   - Check it at https://smith.langchain.com/settings
   - Regenerate if needed

5. ✅ You have an LLM provider configured
   ```bash
   RAG_LLM_PROVIDER=openai  # or ollama
   OPENAI_API_KEY=sk-...     # must be set
   ```

### Common Mistakes

❌ **Using `/query` endpoint**
- This endpoint doesn't use LLMs, so nothing to trace
- Use `/answer` instead

❌ **LLM provider set to "none"**
```bash
RAG_LLM_PROVIDER=none  # Won't make LLM calls!
```

❌ **Missing OpenAI API key**
```bash
# OPENAI_API_KEY not set
# LLM calls will fail, nothing to trace
```

## Next Steps

### To see your first trace:

1. **Set up OpenAI in `.env`:**
   ```bash
   RAG_LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-actual-key
   ```

2. **Build the index:**
   ```bash
   make index
   ```

3. **Make an answer request:**
   ```bash
   curl -X POST http://localhost:8000/answer \
     -H "x-api-key: test-api-key-123" \
     -H "Content-Type: application/json" \
     -d '{"q":"What is this codebase?","top_k":5}'
   ```

4. **Check LangSmith:**
   - Go to https://smith.langchain.com/
   - Look for project "mcp-knowledge-server"
   - You should see a new trace!

## Advanced: Tracing Non-LangChain Code

If you want to trace custom operations (like vector searches), you can use LangSmith's `traceable` decorator:

```python
from langsmith import traceable

@traceable(name="vector_search")
def search_vectors(query: str, top_k: int):
    # Your search logic
    return results
```

This would require additional integration work beyond the current setup.

## Summary

✅ **What We Did:**
- Updated OpenAI client to use `langchain_openai.ChatOpenAI`
- Updated Ollama client to use `langchain_community.llms.Ollama`
- Added LangChain dependencies to `pyproject.toml`

✅ **What Works Now:**
- LangChain automatically detects LangSmith environment variables
- All LLM calls via `/answer` endpoint are traced
- Traces appear in your LangSmith dashboard

✅ **To See Traces:**
- Set `RAG_LLM_PROVIDER=openai` and `OPENAI_API_KEY` in `.env`
- Make requests to `/answer` endpoint
- Check https://smith.langchain.com/ for traces

The project will appear in LangSmith **after the first traced operation runs**!
