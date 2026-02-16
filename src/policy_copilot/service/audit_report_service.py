"""
Audit report generation — JSON and HTML export for query results.

Produces a self-contained audit dossier that records every step of the
pipeline for a given query, suitable for compliance review or dissertation
appendix evidence.
"""
from __future__ import annotations

import json

from policy_copilot.service.schemas import AuditReport, QueryResult

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Policy Copilot — Audit Report {{ report_id }}</title>
<style>
  :root { --bg: #f8f9fa; --card: #fff; --border: #dee2e6; --accent: #2563eb;
          --warn: #dc2626; --ok: #16a34a; --muted: #6b7280; --text: #1f2937; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
         background: var(--bg); color: var(--text); line-height: 1.6;
         max-width: 960px; margin: 0 auto; padding: 2rem 1rem; }
  h1 { font-size: 1.5rem; margin-bottom: .25rem; }
  h2 { font-size: 1.15rem; margin: 1.5rem 0 .5rem; border-bottom: 2px solid var(--accent);
       padding-bottom: .25rem; }
  h3 { font-size: 1rem; margin: 1rem 0 .4rem; }
  .meta { color: var(--muted); font-size: .85rem; margin-bottom: 1.5rem; }
  .card { background: var(--card); border: 1px solid var(--border);
          border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
           font-size: .8rem; font-weight: 600; }
  .badge-ok { background: #dcfce7; color: var(--ok); }
  .badge-warn { background: #fef2f2; color: var(--warn); }
  .badge-info { background: #dbeafe; color: var(--accent); }
  .badge-muted { background: #f3f4f6; color: var(--muted); }
  table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  th, td { text-align: left; padding: .4rem .6rem; border-bottom: 1px solid var(--border); }
  th { background: var(--bg); font-weight: 600; }
  .evidence-text { font-size: .85rem; color: var(--muted); max-height: 120px;
                   overflow-y: auto; white-space: pre-wrap; }
  .contradiction-box { display: flex; gap: 1rem; }
  .contradiction-side { flex: 1; padding: .75rem; border: 1px solid var(--warn);
                         border-radius: 6px; font-size: .85rem; }
  .footer { margin-top: 2rem; text-align: center; color: var(--muted); font-size: .8rem; }
  @media print { body { max-width: 100%; } }
</style>
</head>
<body>

<h1>Policy Copilot — Audit Report</h1>
<p class="meta">Report ID: {{ report_id }} &middot; Generated: {{ generated_at }}</p>

<div class="card">
  <h3>Question</h3>
  <p>{{ question }}</p>
</div>

<div class="card">
  <h3>Answer</h3>
  {% if is_abstained %}
  <span class="badge badge-warn">ABSTAINED</span>
  <p style="margin-top:.5rem">{{ abstention_reason }}</p>
  {% else %}
  <p>{{ answer }}</p>
  {% endif %}
</div>

<h2>Confidence &amp; Metadata</h2>
<div class="card">
<table>
  <tr><th>Max Rerank Score</th><td>{{ confidence_max }}</td></tr>
  <tr><th>Mean Top-3 Rerank</th><td>{{ confidence_mean }}</td></tr>
  <tr><th>Abstain Threshold</th><td>{{ abstain_threshold }}</td></tr>
  <tr><th>Provider / Model</th><td>{{ provider }} / {{ model_name }}</td></tr>
  <tr><th>Backend Requested</th><td>{{ backend_requested }}</td></tr>
  <tr><th>Backend Used</th><td>{{ backend_used }}</td></tr>
  {% if fusion_method %}<tr><th>Fusion Method</th><td>{{ fusion_method }}</td></tr>{% endif %}
  <tr><th>Total Latency</th><td>{{ total_latency_ms }} ms</td></tr>
</table>
</div>

<h2>Latency Breakdown</h2>
<div class="card">
<table>
  <tr><th>Stage</th><th>ms</th></tr>
  <tr><td>Retrieval</td><td>{{ latency.retrieval_ms }}</td></tr>
  <tr><td>Reranking</td><td>{{ latency.rerank_ms }}</td></tr>
  <tr><td>LLM Generation</td><td>{{ latency.llm_gen_ms }}</td></tr>
  <tr><td>Verification</td><td>{{ latency.verify_ms }}</td></tr>
  <tr><td>Contradictions</td><td>{{ latency.contradictions_ms }}</td></tr>
  <tr><td>Critic</td><td>{{ latency.critic_ms }}</td></tr>
</table>
</div>

{% if claims %}
<h2>Claim-by-Claim Verification</h2>
{% if support_rate is not none %}
<p>Support rate: <strong>{{ support_rate_pct }}</strong>
   ({{ supported_count }} / {{ total_claims }})</p>
{% endif %}
{% for c in claims %}
<div class="card">
  <p><strong>Claim {{ c.claim_id }}:</strong> {{ c.text }}</p>
  <p>
    {% if c.supported %}
    <span class="badge badge-ok">Supported</span>
    {% else %}
    <span class="badge badge-warn">Unsupported</span>
    {% endif %}
    <span class="badge badge-muted">Tier {{ c.verification_tier }}</span>
  </p>
  <p style="font-size:.85rem;color:var(--muted);">{{ c.support_rationale }}</p>
  {% if c.citations %}
  <p style="font-size:.85rem;">Citations: {{ c.citations | join(', ') }}</p>
  {% endif %}
  {% if c.evidence_excerpt %}
  <div class="evidence-text">{{ c.evidence_excerpt }}</div>
  {% endif %}
</div>
{% endfor %}
{% endif %}

{% if evidence %}
<h2>Evidence ({{ evidence | length }} paragraphs)</h2>
<table>
  <tr><th>#</th><th>Paragraph ID</th><th>Source</th><th>Page</th>
      <th>Retrieve</th><th>Rerank</th></tr>
  {% for e in evidence %}
  <tr>
    <td>{{ loop.index }}</td>
    <td style="font-family:monospace;font-size:.8rem;">{{ e.paragraph_id }}</td>
    <td>{{ e.source_file }}</td>
    <td>{{ e.page }}</td>
    <td>{{ e.score_retrieve }}</td>
    <td>{{ e.score_rerank }}</td>
  </tr>
  {% endfor %}
</table>
{% endif %}

{% if contradictions %}
<h2>Contradictions ({{ contradictions | length }})</h2>
{% for c in contradictions %}
<div class="card">
  <p><span class="badge badge-warn">{{ c.confidence | upper }}</span>
     Tier {{ c.tier }}: {{ c.rationale }}</p>
  <div class="contradiction-box">
    <div class="contradiction-side">
      <strong>{{ c.paragraph_ids[0] if c.paragraph_ids else '?' }}</strong>
      <p>{{ c.text_a[:300] }}</p>
    </div>
    <div class="contradiction-side">
      <strong>{{ c.paragraph_ids[1] if c.paragraph_ids | length > 1 else '?' }}</strong>
      <p>{{ c.text_b[:300] }}</p>
    </div>
  </div>
</div>
{% endfor %}
{% endif %}

{% if critic_findings %}
<h2>Critic Findings ({{ critic_findings | length }})</h2>
<table>
  <tr><th>Label</th><th>Name</th><th>Paragraph</th><th>Triggers</th></tr>
  {% for f in critic_findings %}
  <tr>
    <td><span class="badge badge-info">{{ f.label }}</span></td>
    <td>{{ f.label_name }}</td>
    <td style="font-family:monospace;font-size:.8rem;">{{ f.paragraph_id }}</td>
    <td>{{ f.triggers | join(', ') }}</td>
  </tr>
  {% endfor %}
</table>
{% endif %}

{% if notes %}
<h2>Pipeline Notes</h2>
<ul>
{% for n in notes %}
  <li>{{ n }}</li>
{% endfor %}
</ul>
{% endif %}

<h2>Configuration Snapshot</h2>
<div class="card">
<pre style="font-size:.8rem;overflow-x:auto;">{{ config_json }}</pre>
</div>

<div class="footer">
  Policy Copilot &middot; Audit Report &middot; {{ generated_at }}
</div>

</body>
</html>
"""


class AuditReportService:
    """Generates structured audit reports from query results."""

    @staticmethod
    def generate_report(query_result: QueryResult) -> AuditReport:
        return AuditReport(query_result=query_result)

    @staticmethod
    def to_json(report: AuditReport, indent: int = 2) -> str:
        return report.model_dump_json(indent=indent)

    @staticmethod
    def to_html(report: AuditReport) -> str:
        try:
            from jinja2 import Template
        except ImportError:
            return (
                "<html><body><h1>Jinja2 not installed</h1>"
                "<p>Install with: pip install jinja2</p>"
                f"<pre>{AuditReportService.to_json(report)}</pre>"
                "</body></html>"
            )

        qr = report.query_result
        cv = qr.claim_verification

        ctx = {
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "question": qr.question,
            "answer": qr.answer,
            "is_abstained": qr.is_abstained,
            "abstention_reason": qr.abstention_reason,
            "confidence_max": f"{qr.confidence_max_rerank:.4f}",
            "confidence_mean": f"{qr.confidence_mean_top3:.4f}",
            "abstain_threshold": f"{qr.abstain_threshold:.2f}",
            "provider": qr.provider,
            "model_name": qr.model,
            "backend_requested": qr.backend_requested,
            "backend_used": qr.backend_used,
            "fusion_method": qr.fusion_method,
            "total_latency_ms": f"{qr.latency.total_ms:.1f}",
            "latency": qr.latency,
            "evidence": [e.model_dump() for e in qr.evidence],
            "claims": [c.model_dump() for c in cv.claims] if cv else [],
            "support_rate": cv.support_rate if cv else None,
            "support_rate_pct": f"{cv.support_rate:.0%}" if cv else "",
            "supported_count": cv.supported_claims if cv else 0,
            "total_claims": (
                cv.supported_claims + cv.unsupported_claims if cv else 0
            ),
            "contradictions": [c.model_dump() for c in qr.contradictions],
            "critic_findings": [f.model_dump() for f in qr.critic_findings],
            "notes": qr.notes,
            "config_json": json.dumps(qr.config_snapshot, indent=2, default=str),
        }

        template = Template(_HTML_TEMPLATE)
        return template.render(**ctx)

    @staticmethod
    def to_markdown(report: AuditReport) -> str:
        qr = report.query_result
        lines = [
            f"# Audit Report: {report.report_id}",
            f"**Generated:** {report.generated_at}",
            "",
            f"## Question\n{qr.question}",
            "",
            f"## Answer\n{qr.answer}",
            "",
        ]
        if qr.is_abstained:
            lines.append(f"**Abstained:** {qr.abstention_reason}\n")

        lines.append("## Evidence\n")
        for i, e in enumerate(qr.evidence, 1):
            lines.append(
                f"{i}. `{e.paragraph_id}` — {e.source_file} p.{e.page} "
                f"(retrieve={e.score_retrieve:.4f}, rerank={e.score_rerank:.4f})"
            )
        lines.append("")

        if qr.claim_verification:
            cv = qr.claim_verification
            lines.append(f"## Claim Verification (support rate: {cv.support_rate:.0%})\n")
            for c in cv.claims:
                status = "Supported" if c.supported else "UNSUPPORTED"
                lines.append(f"- **Claim {c.claim_id}** [{status}]: {c.text}")
            lines.append("")

        if qr.contradictions:
            lines.append(f"## Contradictions ({len(qr.contradictions)})\n")
            for c in qr.contradictions:
                lines.append(f"- {c.rationale} ({c.confidence}) — {c.paragraph_ids}")
            lines.append("")

        if qr.critic_findings:
            lines.append(f"## Critic Findings ({len(qr.critic_findings)})\n")
            for f in qr.critic_findings:
                lines.append(f"- [{f.label}] {f.label_name}: {f.rationale} ({f.paragraph_id})")
            lines.append("")

        return "\n".join(lines)
