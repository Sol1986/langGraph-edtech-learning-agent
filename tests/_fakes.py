"""Shared test doubles used by both tests/unit and tests/integration.

These stand in for ChatOpenAI (structured-output + plain invoke) and the
Qdrant vector store, so tests are deterministic and make zero network calls.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from src import quiz_agent


class _FakeStructuredClient:
    def __init__(self, model: type, factory: Callable[[], Any], recorder: list):
        self._model = model
        self._factory = factory
        self._recorder = recorder

    def invoke(self, messages):
        self._recorder.append((self._model, messages))
        return self._factory()


class FakeLLM:
    """Stands in for ChatOpenAI.

    Routes with_structured_output(Model).invoke(...) calls to canned
    responses keyed by Pydantic model class, so full graph runs are
    deterministic. .invoke(...) (plain, used by /api/hint) returns fixed
    text content.
    """

    def __init__(
        self, responses: dict[type, Callable[[], Any]], plain_content: str = "Here's a hint."
    ):
        self._responses = responses
        self._plain_content = plain_content
        self.structured_calls: list[tuple[type, list]] = []
        self.plain_calls: list[list] = []

    def with_structured_output(self, model: type):
        if model not in self._responses:
            raise KeyError(f"FakeLLM has no canned response registered for {model}")
        return _FakeStructuredClient(model, self._responses[model], self.structured_calls)

    def invoke(self, messages):
        self.plain_calls.append(messages)
        return SimpleNamespace(content=self._plain_content)


@dataclass
class FakeDoc:
    page_content: str
    metadata: dict = field(default_factory=dict)


class FakeRetriever:
    def __init__(self, docs: list[FakeDoc]):
        self._docs = docs
        self.invoke_calls: list[str] = []

    def invoke(self, query: str):
        self.invoke_calls.append(query)
        return self._docs


class FakeVectorStore:
    """Stands in for QdrantVectorStore. Records as_retriever() kwargs so
    tests can assert the retriever isn't capped (see the k=2 regression test).
    """

    def __init__(self, docs: list[FakeDoc] | None = None):
        self._docs = docs if docs is not None else [FakeDoc("some context", {"page_number": 1})]
        self.as_retriever_calls: list[dict | None] = []
        self._last_retriever: FakeRetriever | None = None

    def as_retriever(self, search_kwargs: dict | None = None):
        self.as_retriever_calls.append(search_kwargs)
        self._last_retriever = FakeRetriever(self._docs)
        return self._last_retriever


# --- Canned Pydantic response builders -------------------------------------


def make_chunk_review(**overrides) -> "quiz_agent.ChunkReview":
    defaults = {
        "main_topic": "Test Topic",
        "key_points": ["point 1", "point 2"],
        "important_facts": ["fact 1", "fact 2"],
        "summary": "A concise summary.",
    }
    defaults.update(overrides)
    return quiz_agent.ChunkReview(**defaults)


def make_learning_plan_output(**overrides) -> "quiz_agent.LearningPlanOutput":
    defaults = {
        "course_topic": "Test Topic",
        "learning_plan": (
            "Section 1: Introduction\nSection 2: Basics\nSection 3: Intermediate\n"
            "Section 4: Advanced\nSection 5: Summary"
        ),
    }
    defaults.update(overrides)
    return quiz_agent.LearningPlanOutput(**defaults)


def make_quiz(**overrides) -> "quiz_agent.Quiz":
    questions = overrides.pop("questions", None) or [
        quiz_agent.QuizQuestion(question=f"Question {i}?", topic=f"Section {(i % 5) + 1}")
        for i in range(1, 11)
    ]
    return quiz_agent.Quiz(questions=questions)


def make_expert_feedback(**overrides) -> "quiz_agent.ExpertFeedback":
    defaults = {"suggestions": "Looks good, minor tweaks suggested."}
    defaults.update(overrides)
    return quiz_agent.ExpertFeedback(**defaults)


def make_question_answer(**overrides) -> "quiz_agent.QuestionAnswer":
    defaults = {
        "question": "Question 1?",
        "answer": "Answer 1",
        "explanation": "Answer 1 is correct because of the context.",
        "source_pages": [1],
    }
    defaults.update(overrides)
    return quiz_agent.QuestionAnswer(**defaults)


def make_quiz_completed(**overrides) -> "quiz_agent.Quiz_completed":
    defaults = {
        "question": "Question 1?",
        "correct_answer": "Answer 1",
        "wrong_answers": ["Wrong 1", "Wrong 2", "Wrong 3"],
    }
    defaults.update(overrides)
    return quiz_agent.Quiz_completed(**defaults)


def full_llm_responses() -> dict[type, Callable[[], Any]]:
    """Canned responses covering every structured-output call the full graph makes."""
    return {
        quiz_agent.ChunkReview: make_chunk_review,
        quiz_agent.LearningPlanOutput: make_learning_plan_output,
        quiz_agent.Quiz: make_quiz,
        quiz_agent.ExpertFeedback: make_expert_feedback,
        quiz_agent.QuestionAnswer: make_question_answer,
        quiz_agent.Quiz_completed: make_quiz_completed,
    }


def build_sample_pdf_bytes(num_pages: int = 2) -> bytes:
    """Generates a small real PDF at test time (via reportlab) instead of
    committing a binary fixture."""
    from io import BytesIO

    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    for i in range(1, num_pages + 1):
        c.drawString(72, 720, f"Page {i}: The quick brown fox jumps over the lazy dog.")
        c.drawString(72, 700, f"This is sample content for testing page {i} of the document.")
        c.showPage()
    c.save()
    return buffer.getvalue()
