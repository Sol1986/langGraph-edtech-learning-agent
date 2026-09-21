import pytest

from src import quiz_agent
from tests._fakes import (
    FakeLLM,
    make_chunk_review,
    make_expert_feedback,
    make_learning_plan_output,
    make_question_answer,
    make_quiz,
    make_quiz_completed,
)


def test_document_chunk_reviewer_returns_review(monkeypatch):
    fake_llm = FakeLLM({quiz_agent.ChunkReview: make_chunk_review})
    monkeypatch.setattr(quiz_agent, "llm", fake_llm)

    result = quiz_agent.document_chunk_reviewer({"chunk": {"page_number": 1, "text": "some text"}})

    assert len(result["reviews"]) == 1
    assert isinstance(result["reviews"][0], quiz_agent.ChunkReview)


def test_send_chunks_creates_one_send_per_chunk():
    chunks = [
        {"page_number": 1, "text": "a"},
        {"page_number": 2, "text": "b"},
        {"page_number": 3, "text": "c"},
    ]

    sends = quiz_agent.send_chunks({"chunks": chunks})

    assert len(sends) == 3
    assert all(s.node == "document_chunk_reviewer" for s in sends)
    assert [s.arg for s in sends] == [{"chunk": c} for c in chunks]


def test_learning_plan_builder_raises_without_reviews():
    with pytest.raises(ValueError, match="No reviews were provided"):
        quiz_agent.learning_plan_builder({"reviews": []})


def test_learning_plan_builder_happy_path(monkeypatch):
    fake_llm = FakeLLM({quiz_agent.LearningPlanOutput: make_learning_plan_output})
    monkeypatch.setattr(quiz_agent, "llm", fake_llm)

    result = quiz_agent.learning_plan_builder({"reviews": [make_chunk_review()]})

    assert result["course_topic"] == "Test Topic"
    assert "Section" in result["learning_plan"]


def test_make_questions_includes_human_feedback_in_prompt(monkeypatch):
    fake_llm = FakeLLM({quiz_agent.Quiz: make_quiz})
    monkeypatch.setattr(quiz_agent, "llm", fake_llm)

    state = {
        "learning_plan": "Section 1...Section 5",
        "human_analyst_feedback": "Focus more on section 3.",
        "suggestions": "No expert feedback has been provided yet.",
        "questions": None,
    }
    result = quiz_agent.make_questions(state)

    model, messages = fake_llm.structured_calls[-1]
    assert model is quiz_agent.Quiz
    assert "Focus more on section 3." in messages[0].content

    assert len(result["questions"]) == 10
    assert all(isinstance(q, quiz_agent.QuizQuestion) for q in result["questions"])
    assert all(q.topic for q in result["questions"])


def test_make_questions_formats_previous_questions_as_text(monkeypatch):
    """Regression test: previous_questions used to be a raw list[QuizQuestion]
    dropped straight into an f-string once questions became structured objects."""
    fake_llm = FakeLLM({quiz_agent.Quiz: make_quiz})
    monkeypatch.setattr(quiz_agent, "llm", fake_llm)

    previous = [quiz_agent.QuizQuestion(question="What is X?", topic="Section 1")]
    state = {
        "learning_plan": "Section 1...Section 5",
        "questions": previous,
        "suggestions": "Cover more edge cases.",
    }
    quiz_agent.make_questions(state)

    _, messages = fake_llm.structured_calls[-1]
    assert "What is X?" in messages[0].content


def test_expert_review_returns_feedback_and_increments_turns(monkeypatch):
    fake_llm = FakeLLM({quiz_agent.ExpertFeedback: make_expert_feedback})
    monkeypatch.setattr(quiz_agent, "llm", fake_llm)

    state = {
        "learning_plan": "Section 1...Section 5",
        "course_topic": "Test Topic",
        "questions": [quiz_agent.QuizQuestion(question="Q1", topic="Section 1")],
        "num_turns": 1,
    }
    result = quiz_agent.expert_review(state)

    assert result["suggestions"] == "Looks good, minor tweaks suggested."
    assert result["expert_feedback"] == ["Looks good, minor tweaks suggested."]
    assert result["num_turns"] == 2


def test_route_after_questions_loops_when_num_turns_low():
    assert quiz_agent.route_after_questions({"num_turns": 0, "questions": []}) == "expert_review"
    assert quiz_agent.route_after_questions({"num_turns": 1, "questions": []}) == "expert_review"


def test_route_after_questions_fans_out_at_turn_limit():
    questions = [quiz_agent.QuizQuestion(question=f"Q{i}", topic=f"Section {i}") for i in range(3)]

    sends = quiz_agent.route_after_questions({"num_turns": 2, "questions": questions})

    assert len(sends) == 3
    assert all(s.node == "answer_question" for s in sends)
    assert [s.arg for s in sends] == [
        {"question": "Q0", "topic": "Section 0"},
        {"question": "Q1", "topic": "Section 1"},
        {"question": "Q2", "topic": "Section 2"},
    ]


def test_answer_question_attaches_known_topic(monkeypatch):
    from tests._fakes import FakeVectorStore

    fake_store = FakeVectorStore()
    monkeypatch.setattr(quiz_agent, "_vector_store", fake_store)
    monkeypatch.setattr(quiz_agent, "get_chunk_count", lambda: 5)
    fake_llm = FakeLLM(
        {quiz_agent.QuestionAnswer: lambda: make_question_answer(topic="wrong-guess")}
    )
    monkeypatch.setattr(quiz_agent, "llm", fake_llm)

    result = quiz_agent.answer_question({"question": "What is X?", "topic": "Section 2"})

    # topic is overwritten with the known value from state, not whatever the
    # (fake) LLM guessed.
    assert result["answers"][0].topic == "Section 2"


def test_generate_quiz_attaches_topic_and_source_pages(monkeypatch):
    fake_llm = FakeLLM({quiz_agent.Quiz_completed: make_quiz_completed})
    monkeypatch.setattr(quiz_agent, "llm", fake_llm)

    state = {
        "question": "Q1",
        "correct_answer": "A1",
        "topic": "Section 4",
        "source_pages": [3, 4],
        "explanation": "A1 is correct because of the context.",
    }
    result = quiz_agent.generate_quiz(state)
    quiz = result["quizzes"][0]

    assert quiz.topic == "Section 4"
    assert quiz.source_pages == [3, 4]
    assert quiz.explanation == "A1 is correct because of the context."
    assert len(quiz.wrong_answers) == 3


def test_send_questions_for_wrong_answers_forwards_topic_and_source_pages():
    answers = [
        quiz_agent.QuestionAnswer(
            question="Q1",
            answer="A1",
            explanation="A1 is correct because...",
            source_pages=[1, 2],
            topic="Section 1",
        ),
        quiz_agent.QuestionAnswer(
            question="Q2",
            answer="A2",
            explanation="A2 is correct because...",
            source_pages=[3],
            topic="Section 2",
        ),
    ]

    sends = quiz_agent.send_questions_for_wrong_answers({"answers": answers})

    assert len(sends) == 2
    assert all(s.node == "generate_quiz" for s in sends)
    assert sends[0].arg == {
        "question": "Q1",
        "correct_answer": "A1",
        "topic": "Section 1",
        "source_pages": [1, 2],
        "explanation": "A1 is correct because...",
    }
    assert sends[1].arg == {
        "question": "Q2",
        "correct_answer": "A2",
        "topic": "Section 2",
        "source_pages": [3],
        "explanation": "A2 is correct because...",
    }
