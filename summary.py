"""Deterministic quiz-result summary computation.

No LLM call: the final summary (score, pass/fail, missed questions, topics to
focus on / already understood) is derived purely from the per-question
first-attempt results the frontend already tracked while the learner worked
through the quiz. "No penalty on retry" is reflected by scoring only the
first attempt -- retries let the learner reach the correct answer without
further hurting the score, but the first miss still surfaces here.
"""

from schemas import QuestionResult, SummaryResponse

PASS_THRESHOLD = 0.70


def compute_summary(results: list[QuestionResult]) -> SummaryResponse:
    """Pure function: same inputs always produce the same summary."""
    total = len(results)
    if total == 0:
        return SummaryResponse(
            total=0,
            correct_first_attempt=0,
            score_pct=0.0,
            passed=False,
            wrong_questions=[],
            topics_to_focus=[],
            topics_understood=[],
        )

    correct_first_attempt = sum(1 for r in results if r.first_attempt_correct)
    score_pct = correct_first_attempt / total
    passed = score_pct >= PASS_THRESHOLD

    wrong_questions = [r for r in results if not r.first_attempt_correct]
    topics_to_focus = sorted({r.topic for r in wrong_questions})

    topic_results: dict[str, list[bool]] = {}
    for r in results:
        topic_results.setdefault(r.topic, []).append(r.first_attempt_correct)
    topics_understood = sorted(topic for topic, corrects in topic_results.items() if all(corrects))

    return SummaryResponse(
        total=total,
        correct_first_attempt=correct_first_attempt,
        score_pct=score_pct,
        passed=passed,
        wrong_questions=wrong_questions,
        topics_to_focus=topics_to_focus,
        topics_understood=topics_understood,
    )
