import unittest

from src.inventory_cli import main


class WhenListingInventory(unittest.TestCase):
    def test_prints_one_line_per_item(self) -> None:
        lines: list[str] = []
        main(["list"], out=lines.append)
        self.assertEqual(lines[0].splitlines()[0], "A1  Widget  4")
