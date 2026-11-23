from copy import deepcopy
import unittest

import audit


class AuditChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = audit.load_cases()

    def correct_reply(self, key):
        case = self.cases[key]
        evidence = []
        for role, entries in case["gold"].items():
            proof = entries[0]
            page, row = map(int, proof["at"].split(":"))
            evidence.append({"role": role, "page": page, "row": row, "indices": proof["tokens"],
                             "low_usd": proof["amounts"][0], "high_usd": proof["amounts"][-1]})
        return case, case["expected"] | {"evidence": evidence}

    def test_known_deltas(self):
        expected = {"dt": 8831000, "gddy": 2400000, "infa": -2481000, "qlys": 1833000,
                    "verx": 2865000, "wk": 2879000, "yext": -689000}
        for key, delta in expected.items():
            with self.subTest(key=key):
                case, reply = self.correct_reply(key)
                self.assertEqual(audit.money(case["expected"]["change"]), delta)
                self.assertTrue(audit.score(case, reply)["all_grounded"])

    def test_exact_cancellation(self):
        case, answer = self.correct_reply("dt")
        for f in audit.FIELDS[:2]:
            answer[f] = str(audit.money(answer[f]) + 3_000_000)
        result = audit.score(case, answer)
        self.assertTrue(result["numeric_mask"])
        self.assertTrue(result["exact_cancel"])
        self.assertFalse(result["all_grounded"])

    def test_bad_provenance_is_separate(self):
        case, answer = self.correct_reply("dt")
        answer["evidence"] = deepcopy(answer["evidence"])
        answer["evidence"][0]["row"] += 1
        result = audit.score(case, answer)
        self.assertTrue(result["delta_with_citation_problem_only"])
        self.assertFalse(result["numeric_mask"])

    def test_tolerance_only_and_serialization(self):
        case, answer = self.correct_reply("dt")
        answer["change"] = f'"{answer["change"]}"'
        self.assertTrue(audit.score(case, answer)["all_grounded"])
        answer["change"] = str(audit.money(answer["change"]) + 50_000)
        answer["prior_q4"] = str(audit.money(answer["prior_q4"]) + 1_000_000)
        result = audit.score(case, answer)
        self.assertFalse(result["exact_cancel"])
        self.assertTrue(result["tolerance_only_masks_wrong_level"])


if __name__ == "__main__":
    unittest.main()
