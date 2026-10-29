# Models

Thin adapters so the Gradio app can swap LLM providers via environment variables without rewriting chat or puzzle code.

## Factory

[`factory.py`](factory.py) reads:

| Variable | Default | Role |
| --- | --- | --- |
| `LLM_PROVIDER` | `gateway` | `gateway` or `gemini` |
| `LLM_MODEL` | `openai/gpt-5-mini` | Model id for that provider |
| `GATEWAY_API_KEY` / `GEMINI_API_KEY` | (required) | API key for the chosen provider |

Full app features (especially **puzzle tool calling**) need the Gateway path.

## Adapters

| File | Capabilities |
| --- | --- |
| [`gateway_adapter.py`](gateway_adapter.py) | Streaming chat, structured image/text parse, **tool calling**, in-memory session history, `clear_history` |
| [`gemini_adapter.py`](gemini_adapter.py) | Streaming chat, structured image parse (no tool loop yet) |
| [`interface.py`](interface.py) | Shared `Model` protocol used by the rest of the app |

## Tool-calling loop (Gateway)

Used by the puzzle assistant (`stream_tools`, typically `max_depth=2`):

1. Append the user message to that session’s history.
2. Call the model with the registered tools (Pydantic schemas → function tools).
3. Stream any text deltas to the UI.
4. If the model returns function calls, execute them locally, append the results to history, and call the model again.
5. Repeat until there are no more tool calls, or depth reaches `max_depth`.
6. At max depth, force a final **text-only** completion (tools withheld) so the user always gets an explanation—for example when retrieval keeps failing for a rare theme/rating pair.

`clear_history(session_id)` resets a session when switching between the general and puzzle assistants so each mode stays focused and token use stays bounded.
