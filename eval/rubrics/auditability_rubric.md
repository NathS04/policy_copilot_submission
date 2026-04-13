# Auditability Evaluation Rubric

This rubric defines the five axes used to assess whether Policy Copilot's "audit-ready" claim is measurable. Each axis is scored automatically from evaluation artifacts (golden-set labels, predictions, and run summaries) using `scripts/compute_auditability_scores.py`.

## Axis 1: Evidence Relevance

**Question:** Are the retrieved passages relevant to the query?

**Metric:** `evidence_precision_at_5` and `evidence_recall_at_5` from `summary.json`, computed over queries with gold paragraph IDs.

**Interpretation:**
- High recall = system finds the right evidence
- High precision = system does not flood context with irrelevant passages
- Both must be reported; recall is more critical for audit contexts

## Axis 2: Citation Faithfulness

**Question:** Does each cited passage actually support the claim it is attached to?

**Metric:** `citation_precision` (fraction of system citations that appear in the gold evidence set) and `citation_recall` (fraction of gold evidence paragraphs cited by the system).

**Interpretation:**
- High citation precision = system does not cite unsupportive passages
- High citation recall = system cites all relevant evidence, not just a subset
- `ungrounded_rate` (B3 only) provides a complementary signal from claim verification

## Axis 3: Abstention Correctness

**Question:** Does the system abstain when evidence is insufficient and answer when it is available?

**Metric:** `abstention_accuracy` on the unanswerable golden-set slice. Complemented by false-abstention rate on the answerable slice.

**Interpretation:**
- High abstention accuracy = system correctly identifies unanswerable queries
- False-abstention rate = proportion of answerable queries where the system incorrectly abstains
- Both must be reported to show the precision-recall trade-off of the abstention threshold

## Axis 4: Contradiction Correctness

**Question:** When conflicting evidence exists, does the system surface the contradiction?

**Metric:** `contradiction_recall` (fraction of contradiction-category queries where contradictions are detected) and `contradiction_precision` (fraction of detected contradictions that are in the contradiction category).

**Interpretation:**
- High recall = system catches genuine conflicts
- High precision = system does not over-flag contradictions
- Contradiction handling is a distinguishing feature; both metrics matter

## Axis 5: Failure Mode Attribution

**Question:** When the system fails, can we diagnose why?

**Metric:** Failure-mode taxonomy distribution from `results/tables/failure_taxonomy.csv`, computed by `scripts/classify_errors.py`.

**Interpretation:**
- Taxonomy counts show whether failures are retrieval-dominated, generation-dominated, or abstention-dominated
- Per-baseline comparison reveals which pipeline stages contribute most to errors
- A clean system has most queries in "clean" (no taxonomy category triggered)

## Composite Score

The auditability score is NOT a single number. It is a profile across 5 axes, reported per baseline. This avoids hiding trade-offs behind a composite metric.

The output table (`results/tables/auditability_scores.csv`) reports one row per run with all axis values, enabling side-by-side comparison.
