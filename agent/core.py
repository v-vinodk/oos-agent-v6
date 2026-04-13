import json
import time
import anthropic
from agent.prompts import SYSTEM_PROMPT
from agent.tools import TOOL_DEFINITIONS, execute_tool

client = anthropic.Anthropic()

MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]   # seconds between retries on 529/529


def _call_api(messages: list) -> object:
    """Call the Anthropic API with retry on overload (529) or rate-limit (529)."""
    for attempt in range(MAX_RETRIES):
        try:
            return client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except anthropic.APIStatusError as e:
            if e.status_code in (529, 529) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAYS[attempt]
                time.sleep(wait)
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


def run_agent(user_message: str, history: list) -> tuple[str, list, list]:
    """
    Runs one agentic turn with retry handling.
    Returns (response_text, updated_history, tool_calls_log)
    """
    messages = history + [{"role": "user", "content": user_message}]
    tool_calls_log = []
    max_loops = 10   # prevent infinite tool-call loops

    for _ in range(max_loops):
        response = _call_api(messages)

        # Collect any text from this response
        text_parts = [b.text for b in response.content if hasattr(b, "text")]

        if response.stop_reason == "end_turn":
            text = " ".join(text_parts).strip()
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
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason — return whatever text we have
        text = " ".join(text_parts).strip() or "No response generated."
        messages.append({"role": "assistant", "content": response.content})
        return text, messages, tool_calls_log

    # Exceeded max loops
    return "I reached the maximum number of reasoning steps. Please try a simpler question.", messages, tool_calls_log
