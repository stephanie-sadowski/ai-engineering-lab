"""Lesson 1: Your first API call, and what actually comes back.

Run:  python lessons/01_first_call/main.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lab.common import MODEL, client, header, report_usage, text_of

# --- 1. The simplest possible call --------------------------------------------
header("1. A basic request")
response = client.messages.create(
    model=MODEL,
    max_tokens=16000,  # an upper limit on output, not a target
    messages=[{"role": "user", "content": "In one sentence, what is a large language model?"}],
)
print(text_of(response))
report_usage(response)

# The response is a structured object, not just a string. Look at the pieces:
print("\n  content block types:", [b.type for b in response.content])
print("  request id (log this when debugging):", response._request_id)

# --- 2. System prompts --------------------------------------------------------
# The system prompt sets the role, rules and context for the whole conversation.
header("2. Same question, with a system prompt")
response = client.messages.create(
    model=MODEL,
    max_tokens=16000,
    system="You explain things to a 10-year-old. Use one short analogy. Max 40 words.",
    messages=[{"role": "user", "content": "What is a large language model?"}],
)
print(text_of(response))
report_usage(response)

# --- 3. Effort: trading thoroughness for tokens -------------------------------
# Claude thinks before answering. `effort` controls how hard it thinks.
# Output tokens are the expensive part, so this is a real cost lever.
header("3. Effort levels on a reasoning puzzle")
puzzle = (
    "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. "
    "How much is the ball? Reply with just the answer."
)
for effort in ["low", "high"]:
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": effort},
        messages=[{"role": "user", "content": puzzle}],
    )
    print(f"\n  effort={effort}: {text_of(response).strip()}")
    report_usage(response, effort)

# --- 4. Stop reasons: always check why the model stopped ----------------------
header("4. Hitting max_tokens")
response = client.messages.create(
    model=MODEL,
    max_tokens=60,  # deliberately too small
    messages=[{"role": "user", "content": "Write a 300-word essay on bicycles."}],
)
print(repr(text_of(response)))
report_usage(response)
if response.stop_reason == "max_tokens":
    print("  -> Output was cut off. In real code, raise max_tokens or stream; don't")
    print("     silently treat a truncated answer as complete.")

# --- 5. Production habit: refusal fallbacks -----------------------------------
# Safety classifiers can occasionally decline a request (stop_reason "refusal").
# With fallbacks enabled, the API transparently retries on a suitable model.
header("5. A request with server-side refusal fallbacks enabled")
response = client.beta.messages.create(
    model=MODEL,
    max_tokens=16000,
    betas=["server-side-fallback-2026-07-01"],
    fallbacks="default",
    messages=[{"role": "user", "content": "Name three parts of a bicycle drivetrain."}],
)
if response.stop_reason == "refusal":
    print("  Refused:", response.stop_details)
else:
    print(text_of(response))
    print(f"  served by: {response.model}")
report_usage(response)
