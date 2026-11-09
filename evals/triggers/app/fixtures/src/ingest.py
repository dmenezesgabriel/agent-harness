"""Loads price rows from a CSV export."""


def parse_price(raw: str) -> int:
    try:
        return int(raw)
    except ValueError:
        return 0


def load_rows(lines: list[str]) -> list[dict]:
    rows = []
    for line in lines:
        try:
            sku, price = line.split(",")
            rows.append({"sku": sku, "price_cents": parse_price(price)})
        except Exception:
            pass
    return rows
