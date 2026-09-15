import uuid
from typing import Annotated

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage, SystemMessage

from pdf_ingest import EmptyPdfError, InvalidPdfError, ingest_pdf
from quiz_agent import get_chunk_count, get_vector_store, graph, llm
from schemas import (
    HintRequest,
    HintResponse,
    QuizItem,
    ResumeRequest,
    ResumeResponse,
    SummaryRequest,
    SummaryResponse,
    UploadPdfResponse,
)
from summary import compute_summary

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception) -> JSONResponse:
    """Centralized error handler (per CLAUDE.md): return structured JSON, never a raw traceback."""
    return JSONResponse(status_code=500, content={"error": type(exc).__name__, "detail": str(exc)})


@app.post("/api/upload-pdf", response_model=UploadPdfResponse)
async def upload_pdf(file: Annotated[UploadFile, File()]) -> UploadPdfResponse:
    """Ingests a PDF and starts a new graph thread, running it up to the
    human_feedback interrupt (chunk review -> learning plan)."""
    if file.content_type != "application/pdf":  # PDF MIME type
        raise HTTPException(400, "Only application/pdf uploads are supported.")

    pdf_bytes = await file.read()
    try:
        chunks = await run_in_threadpool(ingest_pdf, pdf_bytes, file.filename or "upload.pdf")
    except (InvalidPdfError, EmptyPdfError) as exc:
        raise HTTPException(422, str(exc)) from exc

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    await run_in_threadpool(graph.invoke, {"chunks": chunks}, config)

    state = graph.get_state(config)
    return UploadPdfResponse(
        thread_id=thread_id,
        course_topic=state.values.get("course_topic"),
        learning_plan=state.values.get("learning_plan"),
        status="awaiting_approval",
    )


@app.post("/api/resume/{thread_id}", response_model=ResumeResponse)
async def resume_thread(thread_id: str, body: ResumeRequest) -> ResumeResponse:
    """HITL resume: writes human feedback into the interrupted thread's state
    targeting the human_feedback node, then resumes to completion.

    Mirrors: graph.update_state(thread, {"human_analyst_feedback": ...}, as_node="human_feedback")
    """
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    if "human_feedback" not in snapshot.next:
        raise HTTPException(409, "Thread is not currently awaiting approval.")

    graph.update_state(
        config,
        {"human_analyst_feedback": body.human_analyst_feedback or "Approved as presented."},
        as_node="human_feedback",
    )
    final_state = await run_in_threadpool(graph.invoke, None, config)

    return ResumeResponse(
        thread_id=thread_id,
        status="completed",
        quizzes=[QuizItem(**q.model_dump()) for q in final_state["quizzes"]],
    )


@app.post("/api/hint", response_model=HintResponse)
async def get_hint(body: HintRequest) -> HintResponse:
    """Generates a hint grounded in the source document (RAG), using the same
    llm and retriever the graph uses, without revealing the correct answer."""
    retriever = get_vector_store().as_retriever(search_kwargs={"k": get_chunk_count()})
    docs = await run_in_threadpool(retriever.invoke, body.question)
    source_pages = sorted({d.metadata["page_number"] for d in docs if "page_number" in d.metadata})
    context = "\n\n".join(d.page_content for d in docs)

    system = SystemMessage(
        content=(
            "You are a supportive tutor helping a learner on a multiple-choice quiz. "
            "Use the provided document context to give a helpful hint WITHOUT stating "
            "or directly implying the correct answer. Encourage them to keep trying "
            "and steer them back to completing the quiz.\n\n"
            f"Document context:\n{context}"
        )
    )
    human = HumanMessage(content=f"Question: {body.question}\nLearner said: {body.user_message}")
    response = await run_in_threadpool(llm.invoke, [system, human])
    return HintResponse(hint=response.content, source_pages=source_pages)


@app.post("/api/summary", response_model=SummaryResponse)
async def get_summary(body: SummaryRequest) -> SummaryResponse:
    """Deterministic, no-LLM summary of the learner's results (see summary.py)."""
    return compute_summary(body.results)


quiz_agent = LangGraphAGUIAgent(
    name="quiz_agent",
    description="An agent that creates a quiz",
    graph=graph,
)


add_langgraph_fastapi_endpoint(
    app=app,
    agent=quiz_agent,
    path="/copilotkit",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
