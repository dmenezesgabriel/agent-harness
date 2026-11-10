"""Processing fee in cents that we pay per payment, by payment method."""


def fee_cents(method: str, amount_cents: int) -> int:
    if method == "card":
        return 30 + amount_cents * 29 // 1000
    elif method == "paypal":
        return 49 + amount_cents * 349 // 10000
    elif method == "bank_transfer":
        return 25
    else:
        raise ValueError("unknown payment method: " + method)
