"""Lesson 3: Structured output - turning messy text into typed data.

Run:  python lessons/03_structured_output/main.py
"""
import sys
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lab.common import MODEL, client, cost_of, header

# Real support inboxes look like this: inconsistent, emotional, incomplete.
EMAILS = [
    "hi my order LB-1004 still hasnt arrived its been like 2 weeks??? need it for a trip saturday",
    "Hello, the rear brake on my Commuter squeaks badly. Bought it in October. Is this covered?",
    "I'd like to cancel my Lumen Plus membership please. Thanks, Ben",
    "YOUR BIKE FELL APART ON THE HIGHWAY. I COULD HAVE DIED. order LB-1003. call me NOW",
    "Do you guys ship to Norway?",
]


# The schema IS the prompt, to a large degree. Field names, types, enums and
# descriptions all tell the model what you want, and the API guarantees the
# output matches - no "please return valid JSON" and hoping.
class Category(str, Enum):
    shipping = "shipping"
    returns = "returns"
    warranty = "warranty"
    membership = "membership"
    safety = "safety"
    other = "other"


class Ticket(BaseModel):
    category: Category
    urgency: int = Field(description="1 (low) to 5 (critical). Safety issues are always 5.")
    order_id: str | None = Field(description="Order id like LB-1234, or null if none given")
    summary: str = Field(description="One neutral sentence, max 15 words")
    needs_human: bool = Field(description="True if an agent should not auto-reply")


header("Triage: unstructured emails -> validated Ticket objects")
tickets: list[Ticket] = []
total = 0.0
for email in EMAILS:
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "low"},  # extraction is easy; don't overpay
        system="You triage customer support emails for Lumen Bikes, a bicycle retailer.",
        messages=[{"role": "user", "content": email}],
        output_format=Ticket,
    )
    ticket = response.parsed_output  # a real Ticket instance, already validated
    tickets.append(ticket)
    total += cost_of(response)

# Because it's typed data, normal code can take over: sort, route, store, chart.
print(f"\n{'urg':<4}{'category':<12}{'order':<9}{'human':<7}summary")
for t in sorted(tickets, key=lambda t: -t.urgency):
    print(f"{t.urgency:<4}{t.category.value:<12}{t.order_id or '-':<9}{str(t.needs_human):<7}{t.summary}")
print(f"\n{len(tickets)} emails triaged for ~${total:.4f}")

urgent = [t for t in tickets if t.urgency >= 4]
print(f"Routing {len(urgent)} urgent ticket(s) to the on-call queue.")
