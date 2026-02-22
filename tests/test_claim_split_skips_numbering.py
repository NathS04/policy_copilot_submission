"""
Numeric-only fragments like '13.' must not become claims.
"""
import unittest
from policy_copilot.verify.claim_split import split_claims


class TestClaimSplitSkipsNumbering(unittest.TestCase):
    def test_bare_number_yields_zero_claims(self):
        claims = split_claims("13. [CITATION: p1]")
        self.assertEqual(len(claims), 0, f"Expected 0 claims, got {claims}")

    def test_number_with_paren_yields_zero_claims(self):
        claims = split_claims("9) [CITATION: p1]")
        self.assertEqual(len(claims), 0, f"Expected 0 claims, got {claims}")

    def test_real_text_after_number_yields_one_claim(self):
        claims = split_claims("13. Some real text [CITATION: p1].")
        self.assertGreaterEqual(len(claims), 1, f"Expected >=1 claim, got {claims}")
        self.assertTrue(any("real text" in c["text"] for c in claims))

    def test_mixed_real_and_numbering(self):
        text = "9. [CITATION: p1]. Encryption is mandatory [CITATION: p1]."
        claims = split_claims(text)
        for c in claims:
            self.assertFalse(
                c["text"].strip().rstrip(".").strip().isdigit(),
                f"Numeric-only claim slipped through: {c}"
            )
