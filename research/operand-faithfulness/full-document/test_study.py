from copy import deepcopy
from decimal import Decimal
import unittest

import layout
import study


def as_reply(case):
    picks = []
    for role, entries in case["gold"].items():
        if entries:
            proof = entries[0]
            page, row = map(int, proof["at"].split(":"))
            picks.append({"role": role, "page": page, "row": row, "indices": proof["tokens"],
                          "low_usd": proof["amounts"][0], "high_usd": proof["amounts"][-1]})
    return {"evidence": picks, **case["expected"]}


class SealedCaseChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = study.load_cases()

    def test_split_and_grounding(self):
        self.assertEqual(len({case["issuer"] for case in self.cases.values()}), 7)
        self.assertEqual(sum(case["split"] == "pilot" for case in self.cases.values()), 3)
        for identifier, case in self.cases.items():
            with self.subTest(case=identifier):
                grades = study.grade_reply(case, as_reply(case))["grades"]["direct"]
                self.assertTrue(all(row["grounded_correct"] for row in grades.values() if row["expected"] is not None))

    def test_reference_numbers(self):
        self.assertEqual({key: Decimal(self.cases[key]["expected"]["change"]) for key in ("rpd", "yelp", "rblx")},
                         {"rpd": 346000, "yelp": -18844000, "rblx": -157000})
        self.assertEqual(Decimal(self.cases["zd"]["expected"]["latest_q4"]), 452135000)
        self.assertIsNone(self.cases["aap"]["expected"]["latest_q4"])

    def test_perturbation_responses(self):
        base = self.cases["rpd"]
        common, single = [study.perturb(base, key) for key in ("common", "latest_shift")]
        self.assertEqual(Decimal(base["expected"]["change"]), Decimal(common["expected"]["change"]))
        self.assertEqual(Decimal(base["expected"]["prior_q4"]) - Decimal(common["expected"]["prior_q4"]), 11000000)
        self.assertEqual(Decimal(base["expected"]["latest_q4"]) - Decimal(common["expected"]["latest_q4"]), 11000000)
        self.assertEqual(Decimal(base["expected"]["change"]) - Decimal(single["expected"]["change"]), 6000000)
        self.assertEqual(base["expected"]["prior_q4"], single["expected"]["prior_q4"])

    def test_same_candidate_partial_publication(self):
        case = self.cases["zd"]
        grades = study.grade_reply(case, as_reply(case))["grades"]
        self.assertIsNone(grades["all_or_nothing"]["latest_q4"]["actual"])
        self.assertTrue(grades["fieldwise"]["latest_q4"]["grounded_correct"])

    def test_whole_vs_partial_and_masking(self):
        case = self.cases["rpd"]
        adjusted = deepcopy(as_reply(case))
        for pick in adjusted["evidence"]:
            if pick["role"].endswith("_ytd"):
                pick["indices"] = [1]
        grades = study.grade_reply(case, adjusted)["grades"]
        self.assertTrue(grades["direct"]["change"]["numeric_exact"])
        self.assertTrue(grades["direct"]["change"]["unsupported_operand"])
        self.assertIsNone(grades["fieldwise"]["change"]["actual"])

    def test_layout_break_and_mixed_units(self):
        case = deepcopy(self.cases["rpd"])
        for line in case["docs"]["prior"]["lines"]:
            if line["page"] > 8 or line["page"] == 8 and line["row"] >= 9:
                line["page"] += 1
        self.assertIn(("9:9", (3,)), layout.candidates(case)["prior_ytd"])
        mixed = layout.candidates(self.cases["yelp"])
        self.assertEqual(mixed["prior_annual"][("15:31", (3, 4))]["scale"], 1_000_000_000)
        self.assertEqual(mixed["prior_q3"][("15:31", (1, 2))]["scale"], 1_000_000)


if __name__ == "__main__":
    unittest.main()
