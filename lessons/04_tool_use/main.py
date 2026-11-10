"""Lesson 4: Tool use - letting the model call your functions.

Run:  python lessons/04_tool_use/main.py            # the loop, written by hand
      python lessons/04_tool_use/main.py --runner   # the same thing with the SDK's tool runner
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from anthropic import beta_tool

from lab import orders
from lab.common import MODEL, client, header, report_usage, text_of

QUESTION = (
    "Order LB-1001: how many days ago was it delivered, and if I return it for "
    "change of mind, how much would I get back? The return fee is $49."
)

# --- Part A: tool definitions as JSON Schema ----------------------------------
# The model only sees the name, description and schema. Write descriptions the
# way you'd brief a new colleague: what it does, when to use it, what it returns.
TOOLS = [
    {
        "name": "lookup_order",
        "description": "Look up an order by id (format LB-1234). Returns item, price, "
                       "delivery date, days since delivery, odometer and membership status.",
        "strict": True,  # guarantees the input matches the schema exactly
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "calculate",
        "description": "Evaluate an arithmetic expression like '1290 - 49'. Use this for "
                       "any math instead of doing it in your head.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
]


def safe_calculate(expression: str) -> float:
    # Never eval() model output with builtins available. Even this is only OK
    # because we whitelist the characters first.
    if not set(expression) <= set("0123456789.+-*/() "):
        raise ValueError("Only numbers and + - * / ( ) are allowed")
    return eval(expression, {"__builtins__": {}})


def execute_tool(name: str, tool_input: dict) -> str:
    if name == "lookup_order":
        return json.dumps(orders.lookup_order(tool_input["order_id"]))
    if name == "calculate":
        return str(safe_calculate(tool_input["expression"]))
    raise ValueError(f"Unknown tool {name}")


def manual_loop() -> None:
    header("Part A: the agentic loop, by hand")
    messages = [{"role": "user", "content": QUESTION}]
    step = 0
    while True:
        step += 1
        response = client.messages.create(
            model=MODEL, max_tokens=16000, tools=TOOLS, messages=messages,
        )
        report_usage(response, f"step {step}")

        # Always append the full assistant turn, tool_use blocks included.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break  # the model answered instead of asking for a tool

        # The model may ask for several tools at once. Run them all, and send
        # every result back in ONE user message.
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  -> model calls {block.name}({block.input})")
            try:
                output, is_error = execute_tool(block.name, block.input), False
            except Exception as e:  # report errors to the model; it can recover
                output, is_error = f"Error: {e}", True
            print(f"  <- {output[:120]}")
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": output, "is_error": is_error})
        messages.append({"role": "user", "content": results})

    print("\nFinal answer:\n" + text_of(response))


# --- Part B: the same tools, the SDK's way ------------------------------------
# @beta_tool builds the JSON schema from the type hints and docstring, and
# the tool runner runs the loop above for you.
@beta_tool
def lookup_order(order_id: str) -> str:
    """Look up an order by id (format LB-1234). Returns item, price, delivery
    date, days since delivery, odometer and membership status.

    Args:
        order_id: The order id, e.g. LB-1001.
    """
    return json.dumps(orders.lookup_order(order_id))


@beta_tool
def calculate(expression: str) -> str:
    """Evaluate an arithmetic expression like '1290 - 49'. Use this for any
    math instead of doing it in your head.

    Args:
        expression: Arithmetic using numbers and + - * / ( ).
    """
    return str(safe_calculate(expression))


def tool_runner() -> None:
    header("Part B: the SDK tool runner")
    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=16000,
        tools=[lookup_order, calculate],
        messages=[{"role": "user", "content": QUESTION}],
        max_iterations=10,  # a safety net against runaway loops
    )
    for message in runner:  # one iteration per model turn
        for block in message.content:
            if block.type == "tool_use":
                print(f"  -> model calls {block.name}({block.input})")
        report_usage(message)
    print("\nFinal answer:\n" + text_of(message))


if __name__ == "__main__":
    tool_runner() if "--runner" in sys.argv else manual_loop()
