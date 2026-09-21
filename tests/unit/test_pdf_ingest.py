import pytest

import src.pdf_ingest as pdf_ingest


def test_extract_pages_returns_page_dicts(sample_pdf_bytes):
    pages = pdf_ingest.extract_pages(sample_pdf_bytes)

    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert "Page 1" in pages[0]["text"]
    assert pages[1]["page_number"] == 2


def test_clean_pages_drops_empty_and_strips_whitespace():
    pages = [
        {"page_number": 1, "text": "  hello world  "},
        {"page_number": 2, "text": "   "},
        {"page_number": 3, "text": ""},
    ]

    cleaned = pdf_ingest.clean_pages(pages)

    assert cleaned == [{"page_number": 1, "text": "hello world"}]


def test_chunk_pages_returns_dict_shape_not_documents():
    """Regression test for the original main.py bug: a dict-shaped chunks list
    was built and then immediately overwritten by LangChain Document objects."""
    clean = [{"page_number": 1, "text": "a" * 50}]

    chunks = pdf_ingest.chunk_pages(clean, chunk_size=20, chunk_overlap=5)

    assert len(chunks) > 1
    for chunk in chunks:
        assert isinstance(chunk, dict)
        assert set(chunk.keys()) == {"page_number", "chunk_number", "text"}
        assert not hasattr(chunk, "page_content")  # not a langchain Document


def test_ingest_pdf_rejects_non_pdf_filename(sample_pdf_bytes):
    with pytest.raises(pdf_ingest.InvalidPdfError, match="Only .pdf files"):
        pdf_ingest.ingest_pdf(sample_pdf_bytes, "notes.txt")


def test_ingest_pdf_rejects_empty_bytes():
    with pytest.raises(pdf_ingest.InvalidPdfError, match="empty"):
        pdf_ingest.ingest_pdf(b"", "empty.pdf")


def test_ingest_pdf_rejects_oversized_file(monkeypatch):
    monkeypatch.setattr(pdf_ingest, "MAX_PDF_SIZE_BYTES", 10)
    with pytest.raises(pdf_ingest.InvalidPdfError, match="exceeds max size"):
        pdf_ingest.ingest_pdf(b"x" * 100, "big.pdf")


def test_ingest_pdf_raises_empty_pdf_error_when_no_extractable_text(monkeypatch, sample_pdf_bytes):
    monkeypatch.setattr(
        pdf_ingest, "extract_pages", lambda pdf_bytes: [{"page_number": 1, "text": ""}]
    )
    with pytest.raises(pdf_ingest.EmptyPdfError, match="No extractable text"):
        pdf_ingest.ingest_pdf(sample_pdf_bytes, "scanned.pdf")


def test_upsert_chunks_deletes_existing_collection_before_recreating(monkeypatch):
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def collection_exists(self, name):
            calls.append(("exists", name))
            return True

        def delete_collection(self, name):
            calls.append(("delete", name))

    def fake_from_documents(**kwargs):
        calls.append(("from_documents", kwargs.get("collection_name")))

    monkeypatch.setattr(pdf_ingest, "QdrantClient", FakeClient)
    monkeypatch.setattr(pdf_ingest.QdrantVectorStore, "from_documents", fake_from_documents)

    pdf_ingest.upsert_chunks([{"page_number": 1, "chunk_number": 1, "text": "hello"}])

    assert calls == [
        ("exists", pdf_ingest.QDRANT_COLLECTION_NAME),
        ("delete", pdf_ingest.QDRANT_COLLECTION_NAME),
        ("from_documents", pdf_ingest.QDRANT_COLLECTION_NAME),
    ]
