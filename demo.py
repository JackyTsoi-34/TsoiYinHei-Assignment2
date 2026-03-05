"""
demo.py — Integration demo for the Text Statistics Tool

Demonstrates the text_statistics tool being called by a DeepSeek-powered AI
agent via OpenAI-compatible function calling, including successful execution
and graceful error handling.

Usage
-----
Option A — environment variable::

    export DEEPSEEK_API_KEY=your_key_here        # Linux / macOS
    $env:DEEPSEEK_API_KEY="your_key_here"        # Windows PowerShell
    python demo.py

Option B — .env file (requires python-dotenv, already in requirements.txt)::

    cp .env.example .env
    # edit .env and paste your key
    python demo.py
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from typing import Any

# Load .env if present -------------------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; key can be set as an env var directly

from openai import OpenAI

from tool import text_stats_tool  # the custom tool built for this assignment

# ---------------------------------------------------------------------------
# DeepSeek client (OpenAI-compatible endpoint)
# ---------------------------------------------------------------------------

_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not _API_KEY:
    sys.exit(
        "\nError: DEEPSEEK_API_KEY environment variable is not set.\n"
        "See README.md — 'Setup' section — for instructions.\n"
    )

client = OpenAI(
    api_key=_API_KEY,
    base_url="https://api.deepseek.com/v1",
)

# ---------------------------------------------------------------------------
# Tool schema for DeepSeek / OpenAI function-calling
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "text_statistics",
            "description": text_stats_tool.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to analyze.",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": (
                            "Number of top keywords to return (1–50). "
                            "Defaults to 10."
                        ),
                    },
                },
                "required": ["text"],
            },
        },
    }
]

SYSTEM_PROMPT = (
    "You are a professional text-analysis assistant. "
    "When asked to analyze text, call the text_statistics tool and then "
    "present the results in a clear, concise, human-readable summary."
)

# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------


def run_agent(user_message: str) -> str:
    """
    Send *user_message* to the DeepSeek agent.

    If the model issues a tool call, the result is automatically fed back
    and a final natural-language reply is returned.  If no tool call is
    made, the model's direct reply is returned.

    Parameters
    ----------
    user_message : str
        The user's instruction / question.

    Returns
    -------
    str
        The agent's final text response.
    """
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    # ── First model call ────────────────────────────────────────────────────
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    msg = response.choices[0].message

    # No tool call → return the model's direct answer
    if not msg.tool_calls:
        return msg.content or ""

    # ── Execute every requested tool call ─────────────────────────────────
    messages.append(msg)

    for tc in msg.tool_calls:
        raw_args: dict[str, Any] = json.loads(tc.function.arguments)
        tool_result = text_stats_tool.execute(**raw_args)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_result, ensure_ascii=False),
            }
        )

    # ── Second model call with tool results ────────────────────────────────
    response2 = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )
    return response2.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Demo scenarios
# ---------------------------------------------------------------------------

_SAMPLE_ARTICLE = textwrap.dedent(
    """\
    Global financial markets experienced turbulence this week as central banks
    signaled further interest rate increases to combat persistent inflation.
    The Federal Reserve, European Central Bank, and Bank of England have all
    indicated that monetary policy will remain restrictive throughout the year.
    Equity indices fell sharply on Wednesday following the announcements, with
    technology stocks bearing the brunt of the sell-off. Analysts warn that
    tighter credit conditions could dampen corporate investment and slow
    economic growth. Consumer confidence indices dropped to a six-month low,
    reflecting widespread anxiety about rising borrowing costs and elevated
    living expenses. Despite the gloomy outlook, labor markets remain resilient,
    with unemployment rates near historic lows across major economies."""
)


def _header(title: str) -> None:
    print("\n" + "=" * 62)
    print(f"  {title}")
    print("=" * 62)


def main() -> None:
    # ── Demo 1: Agent analyzes a news article (API call) ────────────────────
    _header("Demo 1 — Agent calls tool to analyze a news article")
    print(
        "Input (first 120 chars):",
        _SAMPLE_ARTICLE[:120].replace("\n", " ") + " ...\n",
    )
    try:
        reply1 = run_agent(
            f"Please analyze the following business news article and summarize "
            f"its key text statistics:\n\n{_SAMPLE_ARTICLE}"
        )
        print("Agent reply:\n")
        print(textwrap.indent(reply1, "  "))
    except Exception as e:
        print(f"[API unavailable — skipping agent call: {e}]")

    # ── Demo 2: Tool called directly — short text ────────────────────────────
    _header("Demo 2 — Direct tool call (short text, top 5 keywords)")
    short_text = (
        "Innovation drives progress. Companies that invest in research and "
        "development tend to outperform their peers over the long run."
    )
    print(f"Input: {short_text!r}\n")
    result2 = text_stats_tool.execute(text=short_text, top_n=5)
    print("Tool result:")
    print(json.dumps(result2, indent=2))

    # ── Demo 3: Error — empty input ──────────────────────────────────────────
    _header("Demo 3 — Error handling: empty string input")
    result3 = text_stats_tool.execute(text="   ")
    print("Tool result:")
    print(json.dumps(result3, indent=2))

    # ── Demo 4: Error — wrong type ───────────────────────────────────────────
    _header("Demo 4 — Error handling: integer passed instead of string")
    result4 = text_stats_tool.execute(text=42)
    print("Tool result:")
    print(json.dumps(result4, indent=2))

    # ── Demo 5: Agent gracefully handles bad input (API call) ────────────────
    _header("Demo 5 — Agent handles error returned by tool (empty text)")
    try:
        reply5 = run_agent("Please analyze this text for me: ''")
        print("Agent reply:\n")
        print(textwrap.indent(reply5, "  "))
    except Exception as e:
        print(f"[API unavailable — skipping agent call: {e}]")

    _header("All demos completed successfully.")


if __name__ == "__main__":
    main()
