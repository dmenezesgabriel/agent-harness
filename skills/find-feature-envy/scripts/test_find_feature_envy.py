import unittest

from find_feature_envy import find_envy, main


def targets(source: str) -> list[tuple[str, str]]:
    return [(f.name, f.target) for f in find_envy(source, "m.py")]


class FlagsEnvy(unittest.TestCase):
    def test_three_attrs_on_one_param(self) -> None:
        self.assertEqual(targets("def f(u):\n    return u.a + u.b + u.c"), [("f", "u")])

    def test_method_reads_param_not_self(self) -> None:
        src = "class S:\n    def f(self, o):\n        return o.x + o.y + o.z"
        self.assertEqual(targets(src), [("f", "o")])

    def test_method_calls_on_param_count(self) -> None:
        src = "def f(c):\n    return c.get_a() + c.get_b() + c.name"
        self.assertEqual(targets(src), [("f", "c")])


class IgnoresNonEnvy(unittest.TestCase):
    def test_two_attrs_is_under_threshold(self) -> None:
        self.assertEqual(targets("def f(u):\n    return u.a + u.b"), [])

    def test_self_reads_do_not_count(self) -> None:
        src = "class S:\n    def f(self):\n        return self.a + self.b + self.c"
        self.assertEqual(targets(src), [])

    def test_attrs_on_two_params_split(self) -> None:
        src = "def f(u, v):\n    return u.a + u.b + v.c + v.d"
        self.assertEqual(targets(src), [])

    def test_module_constant_is_not_a_param(self) -> None:
        self.assertEqual(targets("def f():\n    return cfg.a + cfg.b + cfg.c"), [])


class Main(unittest.TestCase):
    def test_bad_path_exit_2(self) -> None:
        self.assertEqual(main(["nonexistent-xyz"]), 2)


if __name__ == "__main__":
    unittest.main()
