from schemas import QuestionResult
from summary import compute_summary


def test_all_correct_passes_with_no_focus_topics():
    results = [
        QuestionResult(question="Q1", topic="A", first_attempt_correct=True),
        QuestionResult(question="Q2", topic="B", first_attempt_correct=True),
    ]

    summary = compute_summary(results)

    assert summary.passed is True
    assert summary.score_pct == 1.0
    assert summary.wrong_questions == []
    assert summary.topics_to_focus == []
    assert summary.topics_understood == ["A", "B"]


def test_below_threshold_fails():
    # 1/3 correct = 33% < 70% pass threshold
    results = [
        QuestionResult(question="Q1", topic="A", first_attempt_correct=True),
        QuestionResult(question="Q2", topic="B", first_attempt_correct=False),
        QuestionResult(question="Q3", topic="C", first_attempt_correct=False),
    ]

    summary = compute_summary(results)

    assert summary.passed is False
    assert summary.correct_first_attempt == 1
    assert summary.total == 3


def test_topic_with_mixed_results_is_focus_not_understood():
    results = [
        QuestionResult(question="Q1", topic="A", first_attempt_correct=True),
        QuestionResult(question="Q2", topic="A", first_attempt_correct=False),
    ]

    summary = compute_summary(results)

    assert summary.topics_to_focus == ["A"]
    assert summary.topics_understood == []


def test_topic_fully_correct_is_understood():
    results = [
        QuestionResult(question="Q1", topic="A", first_attempt_correct=True),
        QuestionResult(question="Q2", topic="A", first_attempt_correct=True),
    ]

    summary = compute_summary(results)

    assert summary.topics_understood == ["A"]
    assert summary.topics_to_focus == []


def test_empty_results_does_not_divide_by_zero():
    summary = compute_summary([])

    assert summary.total == 0
    assert summary.correct_first_attempt == 0
    assert summary.score_pct == 0.0
    assert summary.passed is False
    assert summary.wrong_questions == []
    assert summary.topics_to_focus == []
    assert summary.topics_understood == []
