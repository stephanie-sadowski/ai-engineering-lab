# Lesson 1: Your first API call

**Goal:** understand what a model API call is, what it costs, and what comes back.

```bash
python lessons/01_first_call/main.py
```

## Concepts

- **Messages API.** Every Claude feature (tools, structured output, agents) goes through one endpoint: you send a list of `messages` and get back a response made of *content blocks*.
- **Tokens.** Models read and write tokens (roughly ¾ of a word each). You pay per token, and output tokens cost about 5× more than input tokens. `report_usage()` prints both, plus the estimated cost.
- **System prompt.** Instructions that frame the whole conversation: who the model is, what rules it follows, what it knows.
- **Effort.** How hard the model thinks before it answers. Higher effort gives better answers on hard problems and costs more tokens. Don't use more effort than a task needs.
- **Stop reasons.** `end_turn` means the model finished. `max_tokens` means the answer was cut off. `tool_use` comes up in lesson 4. `refusal` means it declined. Production code checks this every time.

## Exercises

1. Change the system prompt in section 2 to make Claude answer as a pirate, then as a lawyer. How far can a system prompt move the output?
2. Run section 3 with `"medium"` and `"max"` too. Write down the output tokens for each level. When is the extra cost worth it?
3. Change `MODEL` in `lab/common.py` to `claude-haiku-5-5`, then re-run. Compare quality and cost.
4. Ask a question that has no correct answer ("What will the weather be on 3 March 2031?") and see how the model handles uncertainty.
