import pytest
from fastapi.testclient import TestClient

import config
import pdf_ingest
import quiz_agent
import server
from tests._fakes import FakeLLM, FakeVectorStore


@pytest.fixture(autouse=True)
def disable_langsmith_tracing(monkeypatch):
    """Tests use fakes for every LLM call, so there's nothing worth tracing --
    and a real .env may set LangSmith credentials, which would otherwise make
    every test attempt (and fail) a real network call."""
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")


@pytest.fixture(autouse=True)
def patch_qdrant_config(monkeypatch):
    """Give require_qdrant_config() deterministic dummy values so tests never
    depend on (or accidentally hit) a real Qdrant instance."""
    monkeypatch.setattr(config, "QDRANT_URL", "http://fake-qdrant.test")
    monkeypatch.setattr(config, "QDRANT_API_KEY", "fake-api-key")


@pytest.fixture(autouse=True)
def reset_vector_store_cache(monkeypatch):
    monkeypatch.setattr(quiz_agent, "_vector_store", None)
    monkeypatch.setattr(quiz_agent, "_chunk_count", None)


@pytest.fixture
def fake_vector_store(monkeypatch):
    """Pre-seeds the vector-store singleton so /api/hint and answer_question
    never touch real Qdrant. Returns the fake store so tests can assert on
    retriever calls."""
    store = FakeVectorStore()
    monkeypatch.setattr(quiz_agent, "_vector_store", store)
    monkeypatch.setattr(quiz_agent, "_chunk_count", 5)
    return store


@pytest.fixture
def patch_llm(monkeypatch):
    """server.py does `from quiz_agent import llm`, which copies the name by
    reference at import time -- graph node functions (defined in quiz_agent.py)
    resolve `llm` through quiz_agent's own module globals, but server.py's
    /api/hint endpoint resolves it through server's own globals. Both must be
    patched to the same fake."""

    def _patch(responses, plain_content="Here's a hint, keep going."):
        fake = FakeLLM(responses, plain_content=plain_content)
        monkeypatch.setattr(quiz_agent, "llm", fake)
        monkeypatch.setattr(server, "llm", fake)
        return fake

    return _patch


@pytest.fixture
def patch_qdrant_upsert(monkeypatch):
    """No-ops out the real Qdrant upsert calls made during PDF ingestion."""
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def collection_exists(self, name):
            return False

        def delete_collection(self, name):
            calls.append(("delete", name))

    def fake_from_documents(**kwargs):
        calls.append(("from_documents", kwargs.get("collection_name")))

    monkeypatch.setattr(pdf_ingest, "QdrantClient", FakeClient)
    monkeypatch.setattr(pdf_ingest.QdrantVectorStore, "from_documents", fake_from_documents)
    return calls


@pytest.fixture
def sample_pdf_bytes():
    from tests._fakes import build_sample_pdf_bytes

    return build_sample_pdf_bytes()


@pytest.fixture
def client():
    return TestClient(server.app)
