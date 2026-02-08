"""
Critic label definitions (L1–L6) for policy language analysis.
"""

# L1–L6 label definitions
LABELS = {
    "L1": {
        "name": "Normative/Loaded Language",
        "description": "Uses emotionally charged, biased, or opinion-loaded words that imply a value judgement rather than stating facts neutrally.",
        "examples": ["obviously", "clearly wrong", "reasonable people agree", "everyone knows"],
    },
    "L2": {
        "name": "Framing Imbalance",
        "description": "Presents only one perspective or uses one-sided quantifiers that minimise alternatives without acknowledging other viewpoints.",
        "examples": ["merely a formality", "only option", "just following orders", "the sole reason"],
    },
    "L3": {
        "name": "Unsupported Claim",
        "description": "Makes a strong factual assertion without evidence, citation, or qualification. Uses certainty language for unverifiable claims.",
        "examples": ["proves beyond doubt", "guarantees success", "ensures compliance", "eliminates all risk"],
    },
    "L4": {
        "name": "Internal Contradiction",
        "description": "Contains conflicting statements within the same text passage (must vs must not, required vs optional for the same thing).",
        "examples": ["X is required ... X is optional", "must be encrypted ... no encryption needed"],
    },
    "L5": {
        "name": "False Dilemma",
        "description": "Presents a complex issue as having only two options when more alternatives exist.",
        "examples": ["either X or Y", "the only two choices", "no alternative exists", "we must choose between"],
    },
    "L6": {
        "name": "Slippery Slope",
        "description": "Claims that one action will inevitably lead to an extreme outcome without justifying the causal chain.",
        "examples": ["will inevitably lead to", "eventually results in", "opens the door to", "sets a dangerous precedent"],
    },
}

LABEL_IDS = list(LABELS.keys())
