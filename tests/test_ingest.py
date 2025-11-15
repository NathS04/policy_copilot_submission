from policy_copilot.ingest.paragraph_ids import generate_paragraph_id
from policy_copilot.ingest.chunking import clean_paragraph

def test_paragraph_id_determinism():
    """Test that the same input produces the exact same ID."""
    doc_id = "test_doc"
    page = 1
    idx = 0
