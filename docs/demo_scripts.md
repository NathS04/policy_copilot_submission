# Demo Storyline Scripts

Three scripted demo journeys for viva presentation. Each demonstrates a core system capability with a specific query, expected behaviour, and screenshot targets.

## Journey 1: Happy Path (Answerable Query with Citations)

**Mode:** Ask

**Query:** "What is the minimum password length?"

**Expected behaviour:**
1. System retrieves relevant paragraphs from the IT Security Addendum
2. Reranker scores evidence above the abstention threshold
3. LLM generates a grounded answer citing specific paragraph IDs
4. Citation pills appear below the answer
5. Evidence rail shows retrieved paragraphs with scores

**Screenshot targets:**
- Chat view with answer and inline citation pills
- Audit Trace view showing claim-by-claim verification with support status
- Evidence rail expanded showing paragraph IDs, retrieval/rerank scores, and copyable citation

**Switch to Audit Trace** after the answer to show the full claim verification breakdown.

---

## Journey 2: Abstention (Insufficient Evidence)

**Mode:** Ask

**Query:** "Are employees allowed to use personal devices for work?"

**Expected behaviour:**
1. System retrieves candidates but none score above the confidence threshold
2. Abstention is triggered (pre-generation confidence gate)
3. UI displays the "Insufficient Evidence" banner with the abstention reason
4. Evidence rail is still visible showing what was retrieved (and why it was insufficient)
5. Export buttons remain available for audit trail

**Screenshot targets:**
- Chat view showing the abstention banner with reason
- Audit Trace view showing abstention status, confidence scores, and threshold
- Evidence rail showing low-scoring retrieved paragraphs

**Key talking point:** The system refuses to answer rather than hallucinate. This is the core safety property of an audit-ready system.

---

## Journey 3: Contradiction Detection

**Mode:** Ask, then switch to Audit Trace

**Query:** Use a contradiction-category query from the golden set (e.g., q_051 or similar).

**Expected behaviour:**
1. System retrieves evidence from multiple documents
2. Contradiction detection identifies conflicting passages
3. UI displays the contradiction banner with side-by-side conflicting excerpts
4. System either abstains or surfaces both positions with a warning

**Screenshot targets:**
- Contradiction banner showing the conflict alert
- Side-by-side display of conflicting evidence passages (text_a vs text_b)
- Audit Trace showing contradiction details with paragraph IDs and rationale

**Key talking point:** The system surfaces disagreement between policy documents rather than silently choosing one interpretation.

---

## Additional Views to Screenshot

Beyond the three journeys, capture screenshots of:

1. **Critic Lens** — Run critic mode on a passage with normative language (e.g., "shall", "must not") to show L1-L6 flag detection
2. **Experiment Explorer** — Browse shipped evaluation runs, compare B2 vs B3 metrics side by side
3. **Reviewer Mode** — Select a query from a shipped run, apply the groundedness/usefulness/citation rubric, show the scoring interface
4. **Audit Export** — Click the JSON/HTML/Markdown download buttons to show the export functionality

## Preparation Checklist

- [ ] Start Streamlit: `streamlit run src/policy_copilot/ui/streamlit_app.py`
- [ ] Ensure the corpus is indexed (or use extractive fallback mode)
- [ ] Have the golden set queries ready for copy-paste
- [ ] Set screen resolution to capture clean screenshots
- [ ] Capture each screenshot at the exact state described above
