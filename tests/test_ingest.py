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

def test_paragraph_id_changes_with_content():
    """Test that different content produces different IDs."""
    id1 = generate_paragraph_id("doc", 1, 0, "Content A")
    id2 = generate_paragraph_id("doc", 1, 0, "Content B")
    assert id1 != id2

def test_clean_paragraph():
    """Test whitespace normalization and hyphen fixing."""
    # Test valid hyphenation fix
    raw = "This is an example of inter- nal hyphenation."
    cleaned = clean_paragraph(raw)
    assert "internal" in cleaned
    
    # Test whitespace collapse
    raw = "This   has    too   many spaces."
    assert clean_paragraph(raw) == "This has too many spaces."
