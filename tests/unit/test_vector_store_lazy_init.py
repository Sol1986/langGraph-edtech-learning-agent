import os
import subprocess
import sys
from pathlib import Path

import pytest

from src import quiz_agent
from tests._fakes import FakeVectorStore

MEMORANG_ROOT = Path(__file__).resolve().parents[2]


def test_import_does_not_eagerly_connect_to_qdrant():
    """Regression test for the original bug: `vector_store = QdrantVectorStore
    .from_existing_collection(...)` used to run at module import time, so
    starting the server before any PDF was uploaded would crash. Spawns a
    fresh interpreter with no Qdrant credentials set and asserts a plain
    `import src.quiz_agent` succeeds -- mirrors the Phase 1 manual check.
    OPENAI_API_KEY and REDIS_URL are kept: quiz_agent needs both at import
    time (OpenAI client construction, RedisSaver.setup())."""
    env = {k: v for k, v in os.environ.items() if k not in ("QDRANT_URL", "QDRANT_API_KEY")}
    result = subprocess.run(
        [sys.executable, "-c", "import src.quiz_agent"],
        cwd=str(MEMORANG_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_get_vector_store_raises_clear_error_when_collection_missing(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("collection not found")

    monkeypatch.setattr(quiz_agent.QdrantVectorStore, "from_existing_collection", boom)

    with pytest.raises(RuntimeError, match="Upload a PDF"):
        quiz_agent.get_vector_store()


def test_get_vector_store_singleton(monkeypatch):
    calls = []

    def fake_from_existing(**kwargs):
        calls.append(kwargs)
        return FakeVectorStore()

    monkeypatch.setattr(
        quiz_agent.QdrantVectorStore, "from_existing_collection", fake_from_existing
    )

    store1 = quiz_agent.get_vector_store()
    store2 = quiz_agent.get_vector_store()

    assert store1 is store2
    assert len(calls) == 1


def test_get_chunk_count_singleton(monkeypatch):
    from types import SimpleNamespace

    calls = []

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            pass

        def count(self, collection_name, exact=True):
            calls.append(collection_name)
            return SimpleNamespace(count=37)

    monkeypatch.setattr(quiz_agent, "QdrantClient", FakeQdrantClient)

    assert quiz_agent.get_chunk_count() == 37
    assert quiz_agent.get_chunk_count() == 37
    assert len(calls) == 1  # cached after the first call


def test_answer_question_retriever_not_capped_at_two(monkeypatch):
    from tests._fakes import FakeLLM, make_question_answer

    fake_store = FakeVectorStore()
    monkeypatch.setattr(quiz_agent, "_vector_store", fake_store)
    monkeypatch.setattr(quiz_agent, "_chunk_count", 37)
    fake_llm = FakeLLM({quiz_agent.QuestionAnswer: make_question_answer})
    monkeypatch.setattr(quiz_agent, "llm", fake_llm)

    quiz_agent.answer_question({"question": "What is X?", "topic": "Section 1"})

    assert fake_store.as_retriever_calls == [{"k": 37}]
