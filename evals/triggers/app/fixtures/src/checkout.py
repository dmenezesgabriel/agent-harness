"""Cart totals and checkout for the shop."""


def order_total(cart: dict) -> int:
    total = 0
    for item in cart["items"]:
        total += item["price_cents"] * item["qty"]
    return total


def apply_discount(total: int, code: str) -> int:
    if code == "SAVE10":
        return total - total // 10
    return total


def checkout(cart: dict, code: str = "") -> dict:
    total = apply_discount(order_total(cart), code)
    return {"total_cents": total, "lines": len(cart["items"])}
