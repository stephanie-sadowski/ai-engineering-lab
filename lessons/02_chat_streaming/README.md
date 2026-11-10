# Lesson 2: A streaming chatbot

**Goal:** build a real chat app, and learn why "memory" is something your code provides.

```bash
python lessons/02_chat_streaming/main.py
```

## Concepts

- **Statelessness.** The model remembers nothing between calls. A conversation is a list you keep and resend every turn, so each turn costs more than the last.
- **Streaming.** Show tokens as they're generated. Time-to-first-token is what users feel.
- **Context stuffing.** The whole handbook goes in the system prompt. This is the simplest form of "grounding" and works well while your data is small. Lesson 5 covers what to do when it isn't.
- **Prompt caching.** The API can cache a repeated prefix, so later reads of it cost 10%. Caching works on an *exact prefix match*: change one character early in the prompt (a timestamp in the system prompt, say) and the cache misses. Watch `cached=` in the usage line.
- **Append-only history.** Append the response's full `content` to your history, and never rewrite earlier turns. Editing history breaks caching and invalidates the model's earlier reasoning.

## Exercises

1. Ask three follow-up questions, then `/cost`. Now remove `cache_control`, repeat, and compare. (Prefixes below a model-specific minimum, between 512 and 4096 tokens, don't get cached at all. Our handbook is small, so `cached=` may stay at 0 until the conversation grows. That's worth seeing for yourself.)
2. Ask something the handbook doesn't cover ("Do you sell skateboards?"). Does it admit that? Tighten the system prompt until it reliably does.
3. Put `datetime.now()` in the system prompt and watch caching break. (This is a common production bug.)
4. Cap the history at the last 10 messages. What does the bot forget?
