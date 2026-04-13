import json
import time
import anthropic
from agent.prompts import SYSTEM_PROMPT
from agent.tools import TOOL_DEFINITIONS, execute_tool

client = anthropic.Anthropic()

MODEL          = "claude-opus-4-6"
MAX_TOKENS     = 16000   # must be > thinking budget
THINKING_BUDGET = 8000   # tokens reserved for internal reasoning
MAX_RETRIES    = 3
RETRY_DELAYS   = [5, 15, 30]


def _call_api(messages: list) -> object:
    """
    Call claude-opus-4-6 with extended thinking enabled.
    Extended thinking lets the model reason through complex OOS queries
    before producing a final answer.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                thinking={
                    "type": "enabled",
                    "budget_tokens": THINKING_BUDGET,
                },
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 503) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise
        except anthropic.RateLimitError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            raise
        except anthropic.APIConnectionError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
                continue
            raise
    raise RuntimeError("API call failed after all retries")


def _extract_text(content_blocks: list) -> str:
    """
    Pull only the visible text blocks from a response.
    Thinking blocks (type='thinking') are kept in history for context
    but never shown to the user.
    """
    return " ".join(
        b.text for b in content_blocks
        if hasattr(b, "text") and getattr(b, "type", "") != "thinking"
    ).strip()


def run_agent(user_message: str, history: list) -> tuple[str, list, list]:
    """
    Runs one agentic turn using claude-opus-4-6 with extended thinking.
    Returns (response_text, updated_history, tool_calls_log).

    Thinking blocks are preserved in the conversation history so the model
    can reference its own reasoning across multi-turn queries, but they are
    stripped from the text returned to the UI.
    """
    messages = history + [{"role": "user", "content": user_message}]
    tool_calls_log = []
    max_loops = 10

    for _ in range(max_loops):
        response = _call_api(messages)

        if response.stop_reason == "end_turn":
            text = _extract_text(response.content)
            messages.append({"role": "assistant", "content": response.content})
            return text, messages, tool_calls_log

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_calls_log.append({"name": block.name, "result": result})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    })
            # Keep full content (including thinking blocks) in history
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user",      "content": tool_results})
            continue

        # Unexpected stop reason
        text = _extract_text(response.content) or "No response generated."
        messages.append({"role": "assistant", "content": response.content})
        return text, messages, tool_calls_log

    return (
        "I reached the maximum number of reasoning steps. Please try a simpler question.",
        messages,
        tool_calls_log,
    )
