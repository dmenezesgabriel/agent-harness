"""`inventory list` prints one line per stocked item."""
import argparse

ITEMS = [
    {"sku": "A1", "name": "Widget", "qty": 4},
    {"sku": "B2", "name": "Gadget", "qty": 0},
]


def format_list(items: list[dict]) -> str:
    return "\n".join(f"{i['sku']}  {i['name']}  {i['qty']}" for i in items)


def main(argv: list[str], out=print) -> int:
    parser = argparse.ArgumentParser(prog="inventory")
    parser.add_argument("command", choices=["list"])
    parser.parse_args(argv)
    out(format_list(ITEMS))
    return 0
