"""Shared helpers used by every lesson.

Keep this file small on purpose: each lesson should show the real SDK calls,
not hide them behind wrappers. These helpers only handle the boring parts
(loading your API key, printing token usage and cost).
"""
from pathlib import Path

import anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

load_dotenv(ROOT / ".env")

# The model every lesson uses. Swap it here to compare models (lesson 6 shows
# how to compare them properly, with an eval instead of vibes).
MODEL = "claude-opus-5-5"

# A small, cheap model for high-volume side jobs such as grading (lesson 6).
JUDGE_MODEL = "claude-haiku-5-5"

# USD per million tokens: (input, output). Prices change, so check
# https://platform.claude.com/docs/en/about-claude/pricing before trusting these.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

# Reads ANTHROPIC_API_KEY from the environment (or from .env, loaded above).
client = anthropic.Anthropic()


def cost_of(response) -> float:
    """Estimated USD cost of one response, from its usage block."""
    price_in, price_out = PRICES.get(response.model, PRICES[MODEL])
    u = response.usage
    # Cache reads are billed at 10% of the input price, cache writes at 125%.
    input_cost = (
        u.input_tokens
        + (u.cache_read_input_tokens or 0) * 0.1
        + (u.cache_creation_input_tokens or 0) * 1.25
    ) * price_in
    return (input_cost + u.output_tokens * price_out) / 1_000_000


def report_usage(response, label: str = "") -> None:
    """Print token counts and estimated cost for a response."""
    u = response.usage
    cached = u.cache_read_input_tokens or 0
    prefix = f"[{label}] " if label else ""
    print(
        f"  {prefix}tokens: in={u.input_tokens} cached={cached} out={u.output_tokens}"
        f" | stop_reason={response.stop_reason} | ~${cost_of(response):.4f}"
    )


def text_of(response) -> str:
    """Join the text blocks of a response. Responses can also hold thinking
    and tool_use blocks, so never just read content[0].text."""
    return "".join(b.text for b in response.content if b.type == "text")


def header(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
