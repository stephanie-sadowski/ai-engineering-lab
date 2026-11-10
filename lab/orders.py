"""A fake order database the tool-use lessons and the agent call into.

In a real system these functions would hit your database or internal APIs.
The point is that the model never touches the data directly: it asks to call
a function, *your code* runs it, and you decide what comes back.
"""
from datetime import date

TODAY = date(2026, 11, 9)

ORDERS = {
    "LB-1001": {"customer": "Ana", "item": "Lumen Commuter bike", "price": 1290.00,
                "kind": "bike", "delivered": date(2026, 10, 28), "odometer_km": 12,
                "member": False, "status": "delivered"},
    "LB-1002": {"customer": "Ben", "item": "Trail helmet", "price": 120.00,
                "kind": "accessory", "delivered": date(2026, 9, 2), "odometer_km": None,
                "member": True, "status": "delivered"},
    "LB-1003": {"customer": "Chloe", "item": "Lumen E-City e-bike", "price": 2890.00,
                "kind": "bike", "delivered": date(2026, 8, 15), "odometer_km": 340,
                "member": False, "status": "delivered"},
    "LB-1004": {"customer": "Dev", "item": "Pannier set", "price": 85.00,
                "kind": "accessory", "delivered": None, "odometer_km": None,
                "member": False, "status": "in transit"},
}

REFUNDS: list[dict] = []  # refunds issued during this run


def lookup_order(order_id: str) -> dict:
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        raise KeyError(f"No order with id {order_id!r}")
    days = (TODAY - order["delivered"]).days if order["delivered"] else None
    return {**order, "delivered": str(order["delivered"]), "days_since_delivery": days}


def issue_refund(order_id: str, amount: float, reason: str) -> dict:
    order = lookup_order(order_id)
    if amount <= 0 or amount > order["price"]:
        raise ValueError(f"Refund must be between 0 and the order price ({order['price']})")
    refund = {"order_id": order_id.upper(), "amount": round(amount, 2), "reason": reason}
    REFUNDS.append(refund)
    return {"status": "refund issued", **refund}
