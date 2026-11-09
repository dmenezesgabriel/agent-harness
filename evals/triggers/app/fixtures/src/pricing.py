"""Unit prices with quantity tiers."""


def unit_price_cents(base_cents: int, qty: int) -> int:
    if qty >= 100:
        return base_cents * 80 // 100
    if qty >= 10:
        return base_cents * 90 // 100
    return base_cents


def line_total_cents(base_cents: int, qty: int) -> int:
    return unit_price_cents(base_cents, qty) * qty
