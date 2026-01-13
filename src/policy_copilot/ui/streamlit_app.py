"""
Policy Copilot – Streamlit UI
Provides:
  • Q&A interface (question → retrieve → generate)
  • Sidebar for uploading PDFs into the corpus
"""

import re
import sys
import traceback
from pathlib import Path

