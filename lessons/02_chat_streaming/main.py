"""Lesson 2: A streaming chatbot with memory and prompt caching.

Run:  python lessons/02_chat_streaming/main.py
Commands inside the chat:  /cost  /reset  /quit
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lab.common import DATA_DIR, MODEL, client, cost_of, report_usage

# A long, stable system prompt: the whole handbook. This is a good fit for
# prompt caching, because it is identical on every turn.
handbook = "\n\n".join(p.read_text() for p in sorted((DATA_DIR / "handbook").glob("*.md")))
SYSTEM = (
    "You are the support assistant for Lumen Bikes. Answer only from the handbook "
    "below. If the handbook doesn't cover something, say so. Be concise and friendly.\n\n"
    f"<handbook>\n{handbook}\n</handbook>"
)

# The API is stateless: it remembers nothing between calls. "Memory" is just
# this list, which we resend in full every turn.
messages: list[dict] = []
total_cost = 0.0

print("Lumen Bikes support chat. Try: 'Can I return a helmet?' (/cost /reset /quit)\n")
while True:
    try:
        user_input = input("you> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if not user_input:
        continue
    if user_input == "/quit":
        break
    if user_input == "/reset":
        messages.clear()
        print("(conversation cleared)\n")
        continue
    if user_input == "/cost":
        print(f"(session cost so far: ~${total_cost:.4f}, {len(messages)} messages)\n")
        continue

    messages.append({"role": "user", "content": user_input})

    # Streaming: print tokens as they arrive instead of waiting for the whole
    # answer. Users perceive this as much faster, even though it isn't.
    print("bot> ", end="", flush=True)
    with client.messages.stream(
        model=MODEL,
        max_tokens=64000,
        output_config={"effort": "low"},  # chat rarely needs deep thinking
        system=SYSTEM,
        # Cache everything up to the last block. On the next turn, the shared
        # prefix (system prompt + earlier turns) is read from cache at 10% of
        # the input price. Watch the "cached=" number grow from turn 2 onward.
        cache_control={"type": "ephemeral"},
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        response = stream.get_final_message()
    print()

    # Append the *full* content (not just the text). It can include thinking
    # blocks the model needs to see again on later turns. Never edit history
    # you've already sent; only append.
    messages.append({"role": "assistant", "content": response.content})
    total_cost += cost_of(response)
    report_usage(response)
    print()
