import operator
from typing import Annotated

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langgraph.checkpoint.redis import RedisSaver

# from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

# Send lets LangGraph dynamically send many chunks to the same reviewer node
from langgraph.types import Send
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from typing_extensions import TypedDict

from src.config import QDRANT_API_KEY, QDRANT_COLLECTION_NAME, QDRANT_URL, require_redis_url

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

llm = ChatOpenAI(model="gpt-5.6-luna")

_vector_store: QdrantVectorStore | None = None
_chunk_count: int | None = None


def get_vector_store() -> QdrantVectorStore:
    """Lazily connect to the shared 'pdf_documents' Qdrant collection.

    Deferred until first use (i.e. until answer_question actually runs) so
    importing this module -- and therefore starting the FastAPI server --
    does not require a PDF to have been uploaded yet.
    """
    global _vector_store
    if _vector_store is None:
        try:
            _vector_store = QdrantVectorStore.from_existing_collection(
                embedding=embeddings,
                collection_name=QDRANT_COLLECTION_NAME,
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
            )
        except Exception as exc:
            raise RuntimeError(
                "No PDF has been ingested yet ('pdf_documents' collection "
                "not found). Upload a PDF via POST /api/upload-pdf first."
            ) from exc
    return _vector_store


def get_chunk_count() -> int:
    """Lazily fetch the total chunk count of the shared Qdrant collection.

    Used to size the retriever's k in answer_question so retrieval is not
    arbitrarily capped below the full ingested document.
    """
    global _chunk_count
    if _chunk_count is None:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        _chunk_count = client.count(QDRANT_COLLECTION_NAME, exact=True).count
    return _chunk_count


# This class defines the exact structure we want the LLM to return for every PDF chunk
class ChunkReview(BaseModel):
    # Main subject discussed in this chunk
    main_topic: str = Field(description="The main topic discussed in the document chunk")

    # Important information found in the chunk
    key_points: list[str] = Field(
        min_length=2, max_length=5, description="The most important points from the chunk"
    )

    # Specific factual statements worth preserving
    important_facts: list[str] = Field(
        min_length=2, max_length=5, description="Important factual claims found in the chunk"
    )

    summary: str = Field(description="A concise summary of the chunk")


# ---------------
class QuizQuestion(BaseModel):
    """A single generated quiz question, tagged with the learning-plan section it tests."""

    question: str = Field(description="The quiz question text")
    topic: str = Field(
        description=(
            "The exact section title (from the 5-section learning plan) this question primarily tests"
        )
    )


class Quiz(BaseModel):
    questions: list[QuizQuestion] = Field(
        min_length=10,
        max_length=10,
    )


class ExpertFeedback(BaseModel):
    suggestions: str


class ChunkState(TypedDict):
    # One individual chunk being reviewed
    chunk: dict


# ---------------
class QuestionAnswer(BaseModel):
    question: str
    answer: str
    explanation: str
    source_pages: list[int]
    # Passed through from the originating QuizQuestion
    # learning-plan section this particular question belongs to.
    topic: str = ""


class QuestionState(TypedDict):
    question: str
    topic: str


class Quiz_completed(BaseModel):
    question: str
    correct_answer: str
    wrong_answers: list[str]
    # Passed through from the matching QuestionAnswer, not derived by the LLM --
    # see generate_quiz, which overwrites whatever the model guesses here.
    explanation: str = ""
    topic: str = ""
    source_pages: list[int] = Field(default_factory=list)


class State(TypedDict):
    chunks: list
    reviews: Annotated[list[ChunkReview], operator.add]
    learning_plan: str
    course_topic: str
    questions: list[QuizQuestion]  # ---------------
    suggestions: str
    num_turns: int
    expert_feedback: Annotated[list[str], operator.add]
    answers: Annotated[list[QuestionAnswer], operator.add]
    quizzes: Annotated[list[Quiz_completed], operator.add]
    human_analyst_feedback: str | None


class LearningPlanOutput(BaseModel):
    course_topic: str = Field(description="A concise topic name that describes what the document teaches")

    learning_plan: str = Field(
        description="A structured 5-section course outline based only on the document reviews"
    )


class QuizState(TypedDict):
    question: str
    correct_answer: str
    topic: str
    source_pages: list[int]
    explanation: str


def human_feedback(state: State):
    """No-op node that should be interrupted on"""


# ---------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------
def document_chunk_reviewer(state: ChunkState):
    # Get the single chunk sent to this node
    chunk = state["chunk"]

    # Force the LLM to return the ChunkReview structure
    structured_llm = llm.with_structured_output(ChunkReview)

    # Tell the model what its job is
    system_message = SystemMessage(
        content="""
        You are a document review assistant.

        Review the provided document chunk carefully.

        Extract only information supported by the document.
        Do not invent information.
        """
    )

    human_message = HumanMessage(
        content=f"""
        Source page: {chunk["page_number"]}

        Document chunk:

        {chunk["text"]}
        """
    )

    # Send the chunk to the LLM
    # The result should now be a ChunkReview Python object
    review = structured_llm.invoke([system_message, human_message])

    return {"reviews": [review]}


def send_chunks(state: State):
    # Create one Send instruction for every chunk.
    return [Send("document_chunk_reviewer", {"chunk": chunk}) for chunk in state["chunks"]]


def learning_plan_builder(state: State):
    # Get the reviews produced by the previous node
    reviews = state.get("reviews")

    # Make sure we actually received reviews
    if not reviews:
        raise ValueError("No reviews were provided. Cannot generate the learning plan.")

    # Convert each Pydantic ChunkReview into readable JSON text
    reviews_text = "\n\n".join(review.model_dump_json(indent=2) for review in reviews)

    system_message = f"""
    You are an expert course outline designer.

    Your job is to analyze the document reviews, identify the main topic,
    and create a structured course outline that will be used to teach students.

    First, determine a concise topic name that accurately describes the
    primary subject taught by the document.

    The topic should:
    - Be specific enough to describe the document's main subject.
    - Be short and suitable as a course or lesson topic.
    - Only use concepts supported by the document reviews.
    - Not mention the document, guide, PDF, or page numbers.

    Then create a course outline divided into exactly 5 sections.

    The 5 sections must collectively cover all important concepts identified
    in the document reviews.

    For each section include:
    - Section title
    - What students will learn in detail
    - Important facts that will be covered

    Requirements:
    - Organize the sections in a logical learning order.
    - Only use information contained in the document reviews.
    - Don't mention the guide or document.
    - Don't mention page numbers.
    - Do not invent topics, concepts, or facts.
    - Do not omit important concepts from the document reviews.
    - Combine related concepts into the same section when appropriate.

    Document reviews:

    {reviews_text}
    """

    structured_llm = llm.with_structured_output(LearningPlanOutput)

    result = structured_llm.invoke([SystemMessage(content=system_message)])

    return {"course_topic": result.course_topic, "learning_plan": result.learning_plan}


def make_questions(state: State):
    outline = state["learning_plan"]
    suggestions = state.get("suggestions", "No expert feedback has been provided yet.")

    human_feedback = state.get("human_analyst_feedback", "No human feedback provided.")

    previous_questions_raw = state.get("questions")
    if previous_questions_raw:
        previous_questions = "\n".join(f"- {q.question}" for q in previous_questions_raw)
    else:
        previous_questions = "No previous questions have been created yet."

    question_instructions = f"""
    You are an expert educational quiz designer.

    Your job is to create a quiz from the learning plan that students
    will use to test their understanding of the material.

    Create exactly 10 quiz questions.
    For each question, return the question text and the topic it tests.

    Requirements:
    - Do not provide answers.
    - Do not provide answer choices.
    - Cover the most important concepts across all sections.
    - Do not focus all questions on one section.
    - Each question should test understanding of a meaningful concept.
    - Avoid duplicate or nearly identical questions.
    - Only use information contained in the course outline.
    - Do not introduce unsupported facts, terminology, or concepts.
    - Use the expert suggestions to improve the previous question set when feedback exists.
    - Each question should test one main idea.
    - Avoid asking students to recall long lists of statistics in a single question.
    - For each question's "topic", use the exact section title of the learning-plan
      section it primarily tests. Do not invent a topic that isn't one of the
      section titles below.

    Learning plan:

    {outline}

    Previous questions:

    {previous_questions}

    Expert suggestions:

    {suggestions}

    Human feedback:

    {human_feedback}

    """
    # We use QuizQuestion starting here.
    # uses your Quiz model, which contains:
    # class Quiz(BaseModel):
    #   questions: list[QuizQuestion]
    # So when the LLM generates the 10 questions, each one becomes:
    quiz_llm = llm.with_structured_output(Quiz)

    system_message = question_instructions

    quiz = quiz_llm.invoke([SystemMessage(content=system_message)])

    return {"questions": quiz.questions}


def expert_review(state: State):
    outline = state["learning_plan"]
    course_topic = state["course_topic"]
    questions = state["questions"]
    questions_text = "\n".join(f"- {q.question}" for q in questions)

    suggestions_message = f"""
    You are an expert on the topic: {course_topic}.

    You are reviewing quiz questions created by an instructional designer.

    Knowledge base:

    {outline}

    Current quiz questions:

    {questions_text}

    Review the questions and suggest improvements.

    Consider:
    - Important concepts that may be missing
    - Questions that are repetitive
    - Questions that may be too easy or unclear
    - Better questions that could test understanding

    Rules:
    1. Use only information from the knowledge base.
    2. Do not introduce external information.
    3. Your role is advisory. The instructional designer decides whether
       to use your suggestions.
    """

    quiz_llm = llm.with_structured_output(ExpertFeedback)

    system_message = suggestions_message

    feedback = quiz_llm.invoke([SystemMessage(content=system_message)])

    return {
        "suggestions": feedback.suggestions,
        "expert_feedback": [feedback.suggestions],
        "num_turns": state.get("num_turns", 0) + 1,
    }


def route_after_questions(state: State):
    if state.get("num_turns", 0) < 2:
        return "expert_review"

    return [
        Send("answer_question", {"question": q.question, "topic": q.topic})
        for q in state["questions"]
    ]


def answer_question(state: QuestionState):
    question = state["question"]
    topic = state["topic"]
    retriever = get_vector_store().as_retriever(search_kwargs={"k": get_chunk_count()})
    docs = retriever.invoke(question)

    answer_message = f"""

    Using only the context provided, answer the question and explain why that
    answer is correct.

    Question:

    {question}

    Context:

    {docs}

    Requirements:
    - "answer": a concise, direct answer to the question (this will be shown
      as a multiple-choice option, so keep it short).
    - "explanation": one to two sentences explaining why that answer is
      correct, grounded only in the context above. Do not just restate the
      answer verbatim.
    - "source_pages": the page numbers from the context that support the answer.

    """
    answer_llm = llm.with_structured_output(QuestionAnswer)

    system_message = answer_message

    answer = answer_llm.invoke([SystemMessage(content=system_message)])

    # creates a new copy of the answer Pydantic object and sets its topic field to the known topic value.
    answer = answer.model_copy(update={"topic": topic})

    return {"answers": [answer]}


def generate_quiz(state: QuizState):
    question = state["question"]
    answer = state["correct_answer"]
    topic = state["topic"]
    source_pages = state["source_pages"]
    explanation = state["explanation"]

    quiz_maker_message = f"""
    Create a multiple choice quiz.

    Question:
    {question}

    Correct answer:
    {answer}

    Generate exactly 3 incorrect but plausible answers.

    Return:
    - the question
    - the correct answer
    - the 3 wrong answers
    """

    answer_llm = llm.with_structured_output(Quiz_completed)

    system_message = quiz_maker_message

    quiz = answer_llm.invoke([SystemMessage(content=system_message)])

    # topic/source_pages/explanation are already known from the upstream
    # creates a new copy of the quiz Pydantic object and sets its topic/source_pages/explanation field to the known topic/source_pages/explanation value.
    quiz = quiz.model_copy(
        update={"topic": topic, "source_pages": source_pages, "explanation": explanation}
    )

    return {"quizzes": [quiz]}


def send_questions_for_wrong_answers(state: State):
    # Create one Send instruction for every question.
    return [
        Send(
            "generate_quiz",
            {
                "question": item.question,
                "correct_answer": item.answer,
                "topic": item.topic,
                "source_pages": item.source_pages,
                "explanation": item.explanation,
            },
        )
        for item in state["answers"]
    ]


# ---------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------

builder = StateGraph(State)
builder.add_node("document_chunk_reviewer", document_chunk_reviewer)
builder.add_node("learning_plan_builder", learning_plan_builder)
builder.add_node("make_questions", make_questions)
builder.add_node("expert_review", expert_review)
builder.add_node("answer_question", answer_question)
builder.add_node("generate_quiz", generate_quiz)
builder.add_node("human_feedback", human_feedback)


# Logic
builder.add_conditional_edges(START, send_chunks, ["document_chunk_reviewer"])
builder.add_edge("document_chunk_reviewer", "learning_plan_builder")
builder.add_edge("learning_plan_builder", "human_feedback")
builder.add_edge("human_feedback", "make_questions")
builder.add_conditional_edges(
    "make_questions", route_after_questions, ["expert_review", "answer_question"]
)
builder.add_edge("expert_review", "make_questions")
builder.add_conditional_edges(
    "answer_question", send_questions_for_wrong_answers, ["generate_quiz"]
)
builder.add_edge("generate_quiz", END)

# memory = MemorySaver()  # replaced with redis

memory = RedisSaver(redis_url=require_redis_url())
memory.setup()

graph = builder.compile(interrupt_before=["human_feedback"], checkpointer=memory)
