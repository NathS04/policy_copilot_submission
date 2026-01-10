"""
Extractive fallback must produce [CITATION: pid] per sentence so claim_split yields citations per claim.
"""
import unittest

from policy_copilot.generate.answerer import Answerer
from policy_copilot.verify.claim_split import split_claims


class TestExtractiveFallbackInlineCitations(unittest.TestCase):
    def test_fallback_claims_have_citations_with_pid(self):
        answerer = Answerer()
        pid = "doc::p42"
        evidence = [
            {"paragraph_id": pid, "text": "Sentence one. Sentence two. Sentence three.", "score": 0.9},
        ]
        resp, _ = answerer._extractive_fallback(evidence[0])
        answer = resp.answer
        self.assertIn("[CITATION:", answer)
        self.assertIn(pid, answer)

        claims = split_claims(answer)
        self.assertGreater(len(claims), 0, "split_claims must return at least one claim")
        for c in claims:
            self.assertIn("citations", c)
            self.assertTrue(
                any(pid in str(x) for x in c["citations"]),
                f"Claim {c.get('claim_id')} must have citations containing {pid!r}"
            )
