# Lesson 3: Structured output

**Goal:** get typed, validated data out of the model so ordinary code can use it.

```bash
python lessons/03_structured_output/main.py
```

## Concepts

- **LLMs as functions.** Most production AI isn't chat. It's `messy text → structured data` inside a larger program: classification, extraction, routing.
- **Schemas as prompts.** Pydantic field names, enums and `description`s guide the model. `messages.parse()` *constrains* the output to match the schema, so you get a validated object back instead of a string you have to parse.
- **Enums over free text.** `Category` limits the model to six values you can `switch` on. Free-text categories drift ("Shipping", "delivery issue", "shipping/delivery").
- **Right-sizing.** Extraction is easy, so `effort: "low"` is enough. Don't pay for deep reasoning you don't need.

## Exercises

1. Add a `sentiment` field (an enum: angry / neutral / happy) and a `language` field. Add a German or Spanish email.
2. Remove the `description` from `urgency`. Do the scores get less consistent? (You're doing an eval by eye. Lesson 6 does it properly.)
3. Write 10 more tricky emails: sarcasm, two problems in one email, a wrong order id format. Where does the triage break?
4. Run the batch with the [Message Batches API](https://platform.claude.com/docs/en/build-with-claude/batch-processing) for 50% off. It's a good fit for high-volume, non-urgent work.
