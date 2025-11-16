from policy_copilot.ingest.paragraph_ids import generate_paragraph_id
from policy_copilot.ingest.chunking import clean_paragraph

def test_paragraph_id_determinism():
    """Test that the same input produces the exact same ID."""
    doc_id = "test_doc"
    page = 1
    idx = 0
    content = "This is a test paragraph."
    
    id1 = generate_paragraph_id(doc_id, page, idx, content)
    id2 = generate_paragraph_id(doc_id, page, idx, content)
    
    assert id1 == id2
    assert "test_doc::p0001::i0000::" in id1

