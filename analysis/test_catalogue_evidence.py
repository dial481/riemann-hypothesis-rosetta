"""Regression checks for mutual blocks and the independent owner-table replay."""
import json
import tempfile
import unittest
from pathlib import Path

from scipy.sparse import csr_matrix

from catalogue_crosscheck import mutual_lines, same_file_order
from catalogue_owner_check import REVERSE_COLUMNS, verify_owner_table
from common import table


class EvidenceTest(unittest.TestCase):
    def test_mutual_order(self):
        source = "-- mutual\ndef before := 0\nmutual\n  inductive A\n  /- end -/\n  inductive B\nend\ndef after := 1"
        lines = {("m", n) for n in mutual_lines(source)}
        self.assertEqual(lines, {("m", n) for n in range(3, 8)})
        for caller, target in ((4, 6), (6, 4), (2, 4), (4, 8)):
            self.assertEqual(same_file_order(("m", caller), ("m", target), lines),
                             "order inconclusive (mutual block)")
        self.assertEqual(same_file_order(("m", 2), ("m", 8), lines), "later in same file")
        self.assertEqual(same_file_order(("m", 8), ("m", 2), lines), "file order permits")

    def test_owner_table_round_trip(self):
        pair = ("a", "b")
        entries = {"a": (["A.field"], []), "b": (["B"], [])}
        owners = {"a": {"A.field": "A"}, "b": {"B": "B"}}
        cards = {k: dict(number=k, title=k, url=f"/{k}/") for k in pair}
        ids = {"A": 0, "B": 1}
        shore = csr_matrix(([1], ([1], [0])), shape=(3, 3))
        pr = csr_matrix(([1, 1], ([1, 2], [2, 0])), shape=(3, 3))
        graphs = {"shore": (shore, ids), "pr": (pr, ids)}
        row = {}
        for side, k in zip(("A_", "B_"), pair):
            row.update({side + col: value for col, value in cards[k].items()})
            row[side + "card_id"] = k
            row[side + "printed_lean_names"] = entries[k][0][0]
            row[side + "exact_name_to_tested_owner"] = json.dumps(owners[k])
        for label, kind, direct in (("shore", "direct", "yes"), ("pr", "transitive", "no")):
            row.update(zip((f"{label}_opposite_{col}" for col in REVERSE_COLUMNS), ("B", "A", kind, direct)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owners.tsv"
            table(path, row, [row.values()])
            verify_owner_table(path, {pair}, entries, owners, cards, graphs)
            for field, invalid in (("A_printed_lean_names", "A"), ("B_printed_lean_names", "A"),
                                   ("shore_opposite_A_dependency", "B"), ("pr_opposite_B_caller", "A"),
                                   ("pr_opposite_edge_direct", "yes"), ("shore_opposite_edge_direct", "no")):
                with self.subTest(field=field):
                    table(path, row, [(row | {field: invalid}).values()])
                    with self.assertRaises(ValueError):
                        verify_owner_table(path, {pair}, entries, owners, cards, graphs)


if __name__ == "__main__":
    unittest.main()
