# Memorang

Turn any PDF into an interactive, AI-generated quiz. Upload a document, review
an AI-drafted learning plan (with a human-in-the-loop approval step), and get
a 10-question multiple-choice quiz grounded in the document's own content —
complete with hints, explanations, and a pass/fail summary.

## How it works

The backend is a [LangGraph](https://langchain-ai.github.io/langgraph/) agent
that pipelines a PDF through review, planning, question generation, expert
critique, and answer grounding before handing quizzes to the frontend. The
graph pauses (`__interrupt__`) after building the learning plan so a human can
approve or edit it before question generation continues.

![Agent graph](./mermaid_diagram.png)

1. **`document_chunk_reviewer`** — the PDF is chunked, and each chunk is sent
   (fanned out in parallel via `Send`) to the LLM to extract its main topic,
   key points, and facts.
2. **`learning_plan_builder`** — the chunk reviews are synthesized into a
   course topic and a structured 5-section learning plan.
3. **`human_feedback`** — the graph interrupts here. A human approves the
   learning plan as-is, or supplies feedback that's fed back into question
   generation.
4. **`make_questions` ⇄ `expert_review`** — 10 quiz questions are drafted from
   the learning plan, then critiqued by an "expert" LLM pass; the critique
   loops back to regenerate an improved question set (twice) before moving on.
5. **`answer_question`** — each question is answered using retrieval-augmented
   generation (RAG) over the document's embeddings in Qdrant, grounding the
   answer and explanation in the source pages.
6. **`generate_quiz`** — each grounded answer is turned into a multiple-choice
   question with 3 plausible wrong answers.

Once the quiz is generated, the frontend also calls `/api/hint` (RAG-grounded
hints that don't give away the answer) and `/api/summary` (a deterministic,
no-LLM pass/fail summary of the learner's first-attempt results).

## Tech stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — HTTP API (`server.py`)
- [LangGraph](https://langchain-ai.github.io/langgraph/) + [LangChain](https://python.langchain.com/) — the quiz-generation agent (`quiz_agent.py`)
- [Qdrant](https://qdrant.tech/) — vector store for document chunk embeddings (`pdf_ingest.py`)
- [OpenAI](https://platform.openai.com/) — chat + embedding models
- [CopilotKit](https://www.copilotkit.ai/) / [AG-UI](https://github.com/ag-ui-protocol/ag-ui) — streams the agent to the frontend

**Frontend** (`quiz-agent/`)
- [Next.js](https://nextjs.org/) 16 + React 19
- CopilotKit React UI/core
- Tailwind CSS

## Project structure

```
.
├── server.py           # FastAPI app: HTTP endpoints + CopilotKit/AG-UI wiring
├── quiz_agent.py        # LangGraph agent: state, nodes, and graph wiring
├── pdf_ingest.py        # PDF → text → chunks → Qdrant embeddings
├── summary.py           # Deterministic scoring/summary logic
├── schemas.py            # Pydantic request/response models
├── config.py             # Centralized env var loading
├── main.py               # Offline CLI to test PDF ingestion without the frontend
├── quiz-agent/            # Next.js frontend
├── tests/
│   ├── unit/              # Fast, no external services
│   └── integration/        # Exercises the FastAPI endpoints
└── mermaid_diagram.png     # Agent graph diagram (rendered above)
```

## Getting started

### Prerequisites
- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Node.js (for the frontend)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Qdrant](https://qdrant.tech/) instance (e.g. [Qdrant Cloud](https://cloud.qdrant.io/)) and API key

### Backend setup

1. Install dependencies:
   ```bash
   uv sync
   ```
2. Copy the env template and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   ```
   OPENAI_API_KEY=
   QDRANT_URL=
   QDRANT_API_KEY=
   ```
3. Run the API server:
   ```bash
   uv run python server.py
   ```
   The API is served at `http://127.0.0.1:8000`.

### Frontend setup

```bash
cd quiz-agent
npm install
npm run dev
```

The frontend expects the backend running at `http://127.0.0.1:8000` and is
itself served at `http://localhost:3000`.

## API endpoints

| Method | Path                        | Description                                              |
|--------|-----------------------------|------------------------------------------------------------|
| POST   | `/api/upload-pdf`           | Ingests a PDF, runs the graph up to the approval interrupt |
| POST   | `/api/resume/{thread_id}`   | Submits (or approves) feedback and resumes the graph to completion |
| POST   | `/api/hint`                 | Returns a RAG-grounded hint for a quiz question, without revealing the answer |
| POST   | `/api/summary`              | Computes a deterministic score/summary from quiz results |
| POST   | `/copilotkit`                | AG-UI/CopilotKit streaming endpoint used by the frontend |

## Testing & linting

```bash
make check        # ruff lint + format check
make test          # unit tests (tests/unit)
make integration    # integration tests (tests/integration)
make verify-phase    # all of the above
```

## Notes

- Uploading a new PDF replaces the shared Qdrant collection (`pdf_documents`)
  — this is a single-document MVP, not per-session/multi-tenant.
- The quiz-generation graph uses `MemorySaver` for checkpointing, so
  in-progress threads are in-memory only and reset on server restart.
