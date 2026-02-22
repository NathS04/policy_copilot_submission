"""Critic package init — exports detection functions and label definitions."""
from policy_copilot.critic.labels import LABELS as LABELS, LABEL_IDS as LABEL_IDS
from policy_copilot.critic.critic_agent import (
    detect as detect,
    detect_heuristic as detect_heuristic,
    detect_llm as detect_llm,
)
