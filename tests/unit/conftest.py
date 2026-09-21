import pytest

from src import config, quiz_agent


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
    """quiz_agent.get_vector_store() caches its result in a module-level global --
    reset it before every test so tests don't leak state into each other."""
    monkeypatch.setattr(quiz_agent, "_vector_store", None)


@pytest.fixture
def sample_pdf_bytes():
    from tests._fakes import build_sample_pdf_bytes

    return build_sample_pdf_bytes()
