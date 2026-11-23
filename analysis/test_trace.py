import unittest

from trace import index_file


class CommandLocalOpenTests(unittest.TestCase):
    def test_local_open_expires_after_the_declaration(self):
        lines = [
            "open Finset",
            "open ThickExists in -- only for the next command",
            "-- a second prefix applies to the same declaration",
            "open Outer.Inner Aux in",
            "",
            "theorem hostThickExists : True := by trivial",
            "theorem following : True := by trivial",
        ]
        host, following = index_file(lines, 0, command_local_opens=True)
        self.assertEqual(host.opens, ("Finset", "ThickExists", "Outer.Inner", "Aux"))
        self.assertEqual(following.opens, ("Finset",))
        self.assertEqual(index_file(lines, 0)[0].opens, ("Finset",))

    def test_intervening_commands_and_scoped_opens(self):
        for prefix in (["open Hidden in", "#check True"], ["open scoped Hidden in"],
                       ["open Hidden (someName) in"]):
            with self.subTest(prefix=prefix):
                decl, = index_file([*prefix, "theorem following : True := by trivial"],
                                   0, command_local_opens=True)
                self.assertEqual(decl.opens, ())


if __name__ == "__main__":
    unittest.main()
