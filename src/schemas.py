"""Pydantic request/response models for server.py's HTTP endpoints.

Kept separate from server.py so the HTTP layer stays thin, the actual

logic lives in pdf_ingest.py, quiz_agent.py, and summary.py.
"""

from pydantic import BaseModel


# Output schema for learning plan
class UploadPdfResponse(BaseModel):
    thread_id: str
    course_topic: str | None = None
    learning_plan: str | None = None
    status: str  # "awaiting_approval"


# schema for human feedback
class ResumeRequest(BaseModel):
    human_analyst_feedback: str | None = None  # None/empty = approve as-is


# schema for each quiz question
class QuizItem(BaseModel):
    question: str
    correct_answer: str
    wrong_answers: list[str]
    explanation: str
    topic: str
    source_pages: list[int]


# schema for answer questions
class ResumeResponse(BaseModel):
    thread_id: str
    status: str  # "completed"
    quizzes: list[QuizItem]


# input schema for hints
class HintRequest(BaseModel):
    question: str
    correct_answer: str
    user_message: str


# output schema for hints
class HintResponse(BaseModel):
    hint: str
    source_pages: list[int]


# schema for question results
class QuestionResult(BaseModel):
    question: str
    topic: str
    first_attempt_correct: bool


# input schema for summary
class SummaryRequest(BaseModel):
    results: list[QuestionResult]


# output schema for summary
class SummaryResponse(BaseModel):
    total: int
    correct_first_attempt: int
    score_pct: float
    passed: bool
    wrong_questions: list[QuestionResult]
    topics_to_focus: list[str]
    topics_understood: list[str]
