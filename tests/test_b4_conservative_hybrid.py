"""Phase E tests: B4 Conservative Hybrid Mode policy module.

Six unit tests using synthetic fixtures. No LLM calls, no file I/O.
"""
from __future__ import annotations


from policy_copilot.service.conservative_hybrid import (
    apply_b4_fallback_policy,
    _question_is_numeric_shape,
    _jaccard_overlap,
)


def _resp(answer, support_rate, question="How long is the notice period?",
          citations=None):
    return {
        "question": question,
        "answer": answer,
        "citations": list(citations or []),
        "support_rate": support_rate,
        "is_abstained": (answer == "INSUFFICIENT_EVIDENCE"),
    }


def _evidence(text, paragraph_id="hr_procedures_manual::p0009::i0000",
              score_rerank=0.9):
    return {
        "paragraph_id": paragraph_id,
        "text": text,
        "score_rerank": score_rerank,
        "score": score_rerank,
    }


# 1. Generative passes → return generative answer
def test_keeps_generative_when_support_rate_above_floor():
    resp = _resp(answer="The standard notice period is 1 month.", support_rate=1.0)
    out = apply_b4_fallback_policy(resp, [_evidence("notice period 1 month")])
    assert out["mode_used"] == "generative"
    assert out["fallback_reason"] is None
    assert out["answer"] == "The standard notice period is 1 month."


# 2. Support gate fired but evidence is strong → extractive fallback
def test_falls_back_to_extractive_when_support_low_but_evidence_strong():
    resp = _resp(answer="INSUFFICIENT_EVIDENCE", support_rate=0.5,
                 question="How long is the notice period?")
    top = _evidence(
        text="The standard notice period is 1 month for employees below senior management.",
        paragraph_id="hr_procedures_manual::p0009::i0000",
        score_rerank=0.85,
    )
    out = apply_b4_fallback_policy(resp, [top])
    assert out["mode_used"] == "extractive_fallback"
    assert "1 month" in out["answer"]
    assert out["citations"] == ["hr_procedures_manual::p0009::i0000"]
    assert out["is_abstained"] is False


# 3. Support gate fired AND rerank below threshold → abstain
def test_abstains_when_rerank_below_threshold():
    resp = _resp(answer="INSUFFICIENT_EVIDENCE", support_rate=0.5)
    top = _evidence(text="unrelated text about HR", score_rerank=0.20)
    out = apply_b4_fallback_policy(resp, [top])
    assert out["mode_used"] == "abstained"
    assert "top_rerank" in out["fallback_reason"]


# 4. No retrieved evidence at all → abstain
def test_abstains_when_no_evidence():
    resp = _resp(answer="INSUFFICIENT_EVIDENCE", support_rate=None)
    out = apply_b4_fallback_policy(resp, [])
    assert out["mode_used"] == "abstained"
    assert out["fallback_reason"] == "no_retrieved_evidence"


# 5. Extractive fallback never returns uncited text
def test_extractive_fallback_always_has_citation():
    resp = _resp(answer="INSUFFICIENT_EVIDENCE", support_rate=0.3,
                 question="What is the maximum probation period?")
    top = _evidence(
        text="A formal probation review is conducted at 3 months and 6 months.",
        paragraph_id="hr_procedures_manual::p0004::i0002",
        score_rerank=0.75,
    )
    out = apply_b4_fallback_policy(resp, [top])
    assert out["mode_used"] in ("extractive_fallback", "abstained")
    if out["mode_used"] == "extractive_fallback":
        assert out["citations"], "extractive fallback must include at least one citation"
        # The answer must come from a retrieved paragraph (we don't paraphrase).
        assert out["answer"] == top["text"]


# 6. Policy does not consult golden labels
def test_policy_module_does_not_import_golden_set():
    import policy_copilot.service.conservative_hybrid as mod
    src = open(mod.__file__).read()
    forbidden = ["golden_set", "gold_paragraph_ids", "golden_path",
                 "is_answerable_label", "category =="]
    for token in forbidden:
        assert token not in src, f"conservative_hybrid module references {token!r}"


# Helper-function sanity checks
def test_jaccard_overlap_helper():
    assert _jaccard_overlap("notice period resignation", "the standard notice period is") > 0.0
    assert _jaccard_overlap("totally unrelated", "different words entirely") == 0.0


def test_numeric_shape_detection():
    assert _question_is_numeric_shape("How long is the notice period?")
    assert _question_is_numeric_shape("How many days?")
    assert _question_is_numeric_shape("What is the maximum probation period?")
    assert not _question_is_numeric_shape("Is there a grievance procedure?")
