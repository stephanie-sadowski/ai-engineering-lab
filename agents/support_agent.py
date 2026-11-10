"""Lumen Bikes support agent - the capstone that combines every lesson.

It searches the handbook (RAG), looks up orders, and can issue refunds behind
a human-approval gate. Run it:

    python agents/support_agent.py
    python agents/support_agent.py "I want to return order LB-1001, I changed my mind"
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anthropic import beta_tool

from lab import orders
from lab.common import MODEL, client, cost_of, text_of
from lab.retrieval import format_context, get_index

SYSTEM = f"""You are the customer support agent for Lumen Bikes. Today is {orders.TODAY}.

How you work:
- Look up policy with search_handbook before stating any policy. Never rely on memory.
- Look up the order before making any decision about it.
- Check every eligibility rule (return window, membership, odometer, condition) against
  the order data, and show the customer the numbers you used.
- Only call issue_refund when the policy clearly allows it. A human approves every refund;
  if they decline, tell the customer a specialist will follow up.
- If something isn't covered by the handbook, say so and offer to escalate. Don't invent policy.
- Be warm and brief."""

# Approval is a policy decision made in code, not left to the model.
AUTO_APPROVE = "--yes" in sys.argv


@beta_tool
def search_handbook(query: str) -> str:
    """Search the Lumen Bikes policy handbook (returns, shipping, warranty,
    membership, repairs). Returns the most relevant sections with ids.

    Args:
        query: Keywords describing the policy you need, e.g. "return window bike".
    """
    hits = get_index().search(query, top_k=3)
    return format_context(hits) if hits else "No matching handbook sections."


@beta_tool
def lookup_order(order_id: str) -> str:
    """Look up an order by id (format LB-1234): item, price, kind (bike or
    accessory), delivery date, days since delivery, odometer km, and whether
    the customer is a Lumen Plus member.

    Args:
        order_id: The order id, e.g. LB-1001.
    """
    try:
        return json.dumps(orders.lookup_order(order_id))
    except KeyError as e:
        return f"Error: {e}. Ask the customer to double-check the order id."


@beta_tool
def issue_refund(order_id: str, amount: float, reason: str) -> str:
    """Issue a refund to the original payment method. Requires human approval.
    Only call after confirming eligibility against the handbook and order data.

    Args:
        order_id: The order id.
        amount: Refund amount in USD, after any fees.
        reason: Short justification citing the policy that applies.
    """
    print(f"\n  ⚠️  APPROVAL NEEDED: refund ${amount:.2f} on {order_id}\n      reason: {reason}")
    approved = AUTO_APPROVE or input("      approve? [y/N] ").strip().lower() == "y"
    if not approved:
        return "Refund declined by the human reviewer. Do not retry; escalate to a specialist."
    try:
        return json.dumps(orders.issue_refund(order_id, amount, reason))
    except (KeyError, ValueError) as e:
        return f"Error: {e}"


TOOLS = [search_handbook, lookup_order, issue_refund]


def run(messages: list) -> tuple[str, float]:
    """Run the agent on a conversation and return (reply, cost). New messages
    are appended to `messages` in place, so the conversation keeps going."""
    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        system=SYSTEM,
        tools=TOOLS,
        messages=messages,
        max_iterations=12,
    )
    cost, last = 0.0, None
    for message in runner:
        cost += cost_of(message)
        for block in message.content:
            if block.type == "tool_use":
                print(f"  · {block.name}({json.dumps(block.input)})")
        # Mirror the runner's history so the next user turn has full context.
        # generate_tool_call_response() is cached: the runner reuses it, so
        # each tool still runs exactly once.
        messages.append({"role": "assistant", "content": message.content})
        tool_results = runner.generate_tool_call_response()
        if tool_results:
            messages.append(tool_results)
        last = message
    return text_of(last), cost


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--yes"]
    messages: list = []
    total = 0.0
    first = " ".join(args) if args else None
    print("Lumen Bikes support agent. Try: 'Can I return order LB-1001? I changed my mind.'\n")
    while True:
        user_input = first or input("you> ").strip()
        first = None
        if user_input in ("", "/quit"):
            break
        messages.append({"role": "user", "content": user_input})
        reply, cost = run(messages)
        total += cost
        print(f"\nagent> {reply}\n  (~${cost:.4f} this turn, ~${total:.4f} total)\n")
        if args:
            break


if __name__ == "__main__":
    main()
