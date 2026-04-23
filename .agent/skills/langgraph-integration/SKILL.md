---
name: langgraph-integration
description: Use when building or modifying the LangGraph AI orchestration layer. Covers GLM-5.1 integration, thinking mode, tool calling, Langfuse tracing.
---

## GLM-5.1 Integration Pattern

```python
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "glm-5.1"),
    openai_api_key=os.getenv("MODEL_API_KEY"),
    openai_api_base=os.getenv("MODEL_BASE_URL"),
    temperature=0.3,
    max_tokens=4096,
)
```

## Thinking Mode
GLM-5.1 supports thinking via `extra_body={"thinking": {"type": "enabled"}}`.
The response includes `reasoning_content` separate from `content`.
For streaming: check `chunk.additional_kwargs.get("reasoning_content", "")`.

## Langfuse Tracing
Wrap every LLM call with Langfuse callback:
```python
from langfuse.callback import CallbackHandler
handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)
response = llm.invoke(messages, config={"callbacks": [handler]})
```

## LangGraph Rules
- Keep the graph thin — only AI-heavy steps
- Deterministic math stays in FastAPI services, NOT in graph nodes
- Graph nodes: extract_quotes, build_context, reason_recommendation, stream_analyst
- FastAPI services: cost_engine, ranking_engine, hedge_calculator, validation
