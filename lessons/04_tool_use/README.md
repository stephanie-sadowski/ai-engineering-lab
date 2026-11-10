# Lesson 4: Tool use

**Goal:** understand the loop at the heart of every AI agent.

```bash
python lessons/04_tool_use/main.py            # loop written by hand: read this first
python lessons/04_tool_use/main.py --runner   # same thing, SDK-managed
```

## Concepts

- **The model doesn't run anything.** It returns a `tool_use` block that says "please call `lookup_order` with `{order_id: 'LB-1001'}`". *Your code* decides whether to run it, runs it, and sends back a `tool_result`.
- **The agentic loop.** Call the model, run the tools it asks for, send back the results, repeat until `stop_reason != "tool_use"`. Every agent framework is a variation on this `while` loop.
- **Tool descriptions are prompts.** The model chooses tools only from their name, description and schema, so vague descriptions lead to wrong tool calls.
- **Errors are information.** Return failures as `is_error: True` results instead of crashing. The model will often fix its own mistake, for example by retrying with a corrected order id.
- **Give the model a calculator.** Models can do arithmetic but sometimes slip. A deterministic tool is cheap insurance.
- **Security.** Tool inputs come from the model, and indirectly from whatever text it read. Validate them like user input. `safe_calculate` whitelists characters before it evaluates anything.

## Exercises

1. Ask about order `LB-9999`. Watch the error go back to the model and see how it responds.
2. Add a `check_return_eligibility(order_id)` tool that applies the rules in `data/handbook/returns.md` in code. When should business rules live in code rather than in a prompt?
3. Count the steps for a question that needs two orders. Does the model call tools in parallel?
4. Remove `"strict": True` and the calculator description. Does behaviour change?
