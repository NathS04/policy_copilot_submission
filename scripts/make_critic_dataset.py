#!/usr/bin/env python3
"""
Helper for creating/extending the critic evaluation dataset.
Modes:
  --manual (default): creates template files and instructions
  --llm_generate (optional): generates manipulated variants from neutral text
"""
import argparse
import json
import sys
from pathlib import Path


def _create_templates(output_dir: Path):
    """Create empty template files for manual dataset construction."""
    neutral_dir = output_dir / "neutral"
    manip_dir = output_dir / "manipulated"
    neutral_dir.mkdir(parents=True, exist_ok=True)
    manip_dir.mkdir(parents=True, exist_ok=True)

    # check if existing files have content
    neutral_path = neutral_dir / "critic_snippets.jsonl"
    manip_path = manip_dir / "critic_snippets.jsonl"
    manifest_path = output_dir / "critic_manifest.csv"

    existing_neutral = 0
    existing_manip = 0
    if neutral_path.exists():
        with open(neutral_path) as f:
            existing_neutral = sum(1 for _ in f)
    if manip_path.exists():
        with open(manip_path) as f:
            existing_manip = sum(1 for _ in f)

    print(f"[✓] Dataset directory: {output_dir}")
    print(f"    Neutral snippets: {existing_neutral}")
    print(f"    Manipulated snippets: {existing_manip}")
    print()
    print("Instructions for manual creation:")
    print("=" * 60)
    print()
    print("1. Neutral snippets (no labels):")
    print(f"   Edit: {neutral_path}")
    print('   Format: {"snippet_id":"s_NNNN","source":"handbook","text":"...","labels":[]}')
    print()
    print("2. Manipulated snippets (with labels):")
    print(f"   Edit: {manip_path}")
    print('   Format: {"snippet_id":"s_NNNN","source":"handbook","text":"...","labels":["L1","L3"]}')
    print()
    print("Labels:")
    print("  L1 = Normative/loaded language")
    print("  L2 = Framing imbalance")
    print("  L3 = Unsupported claim")
    print("  L4 = Internal contradiction")
    print("  L5 = False dilemma")
    print("  L6 = Slippery slope")
    print()
    print("3. Update manifest:")
    print(f"   Edit: {manifest_path}")
    print("   Columns: snippet_id,version(neutral|manipulated),labels,notes")
    print()
    print("Requirements:")
    print("  - At least 25 neutral + 25 manipulated = 50 total")
    print("  - Every label L1–L6 must appear ≥8 times in manipulated set")


def _llm_generate(output_dir: Path, n: int = 5):
    """Generate manipulated variants from neutral snippets using LLM."""
    try:
        from policy_copilot.verify.llm_judges import _call_llm, _parse_json_response
    except Exception as e:
        print(f"[!] Cannot load LLM (no API key?): {e}")
        sys.exit(1)

    neutral_path = output_dir / "neutral" / "critic_snippets.jsonl"
    if not neutral_path.exists():
        print(f"[!] No neutral snippets found at {neutral_path}")
        return

    # load neutral snippets
    neutrals = []
    with open(neutral_path) as f:
        for line in f:
            try:
                neutrals.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    if not neutrals:
        print("[!] No neutral snippets to manipulate")
        return

    # find next snippet ID
    manip_path = output_dir / "manipulated" / "critic_snippets.jsonl"
    existing = 0
    if manip_path.exists():
        with open(manip_path) as f:
            existing = sum(1 for _ in f)

    system = """You are a policy text manipulator for evaluation purposes.
Given a neutral policy snippet, create a manipulated version that contains specific language issues.
You MUST keep the meaning close but inject the target pattern.

Labels:
L1 = Normative/loaded language (emotionally charged words)
L2 = Framing imbalance (one-sided perspective)
L3 = Unsupported claim (unverifiable strong assertions)
L4 = Internal contradiction (conflicting statements)
L5 = False dilemma (only two options presented)
L6 = Slippery slope (unjustified causal chain)

Return ONLY valid JSON:
{"text": "manipulated text", "labels": ["L1", "L3"]}"""

    import random
    random.seed(42)
    label_targets = ["L1", "L2", "L3", "L4", "L5", "L6"]
    samples = neutrals[:n] if n <= len(neutrals) else neutrals

    generated = []
    for i, snippet in enumerate(samples):
        # pick 1-2 target labels
        target = random.sample(label_targets, min(2, len(label_targets)))
        user = f"""Manipulate this neutral text to contain labels {target}:

Original: {snippet['text']}

Return JSON only:"""

        try:
            raw = _call_llm(system, user)
            result = _parse_json_response(raw)
            if "text" in result and "labels" in result:
                sid = f"s_{2000 + existing + i:04d}"
                entry = {
                    "snippet_id": sid,
                    "source": "handbook",
                    "text": result["text"],
                    "labels": result["labels"],
                }
                generated.append(entry)
                print(f"  [+] Generated {sid}: {result['labels']}")
        except Exception as e:
            print(f"  [!] Failed on snippet {snippet['snippet_id']}: {e}")

    if generated:
        manip_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manip_path, "a") as f:
            for entry in generated:
                f.write(json.dumps(entry) + "\n")
        print(f"\n[✓] Appended {len(generated)} manipulated snippets to {manip_path}")
        print("    Remember to update critic_manifest.csv!")


def main():
    parser = argparse.ArgumentParser(description="Create/extend critic evaluation dataset.")
    parser.add_argument("--mode", choices=["manual", "llm_generate"], default="manual")
    parser.add_argument("--output_dir", default="data/handbook/variants",
                        help="Base directory for critic dataset")
    parser.add_argument("--n", type=int, default=5,
                        help="Number of snippets to generate in llm_generate mode")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    if args.mode == "manual":
        _create_templates(output_dir)
    elif args.mode == "llm_generate":
        _llm_generate(output_dir, n=args.n)


if __name__ == "__main__":
    main()
