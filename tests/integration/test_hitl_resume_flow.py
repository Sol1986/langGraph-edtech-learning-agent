from src import quiz_agent
from tests._fakes import full_llm_responses


def _upload(client, sample_pdf_bytes) -> str:
    response = client.post(
        "/api/upload-pdf",
        files={"file": ("lesson.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()["thread_id"]


def test_resume_before_upload_returns_409(client):
    response = client.post("/api/resume/does-not-exist", json={"human_analyst_feedback": None})
    assert response.status_code == 409


def test_upload_pauses_graph_at_human_feedback(
    client, patch_llm, patch_qdrant_upsert, sample_pdf_bytes
):
    patch_llm(full_llm_responses())

    thread_id = _upload(client, sample_pdf_bytes)

    config = {"configurable": {"thread_id": thread_id}}
    assert quiz_agent.graph.get_state(config).next == ("human_feedback",)


def test_full_hitl_cycle_pauses_then_resumes(
    client, patch_llm, patch_qdrant_upsert, fake_vector_store, sample_pdf_bytes
):
    patch_llm(full_llm_responses())

    thread_id = _upload(client, sample_pdf_bytes)

    response = client.post(f"/api/resume/{thread_id}", json={"human_analyst_feedback": None})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["quizzes"]) == 10
    for quiz in body["quizzes"]:
        assert len(quiz["wrong_answers"]) == 3
        assert quiz["topic"]


def test_resume_writes_feedback_into_human_analyst_feedback_state(
    client, patch_llm, patch_qdrant_upsert, fake_vector_store, sample_pdf_bytes
):
    patch_llm(full_llm_responses())

    thread_id = _upload(client, sample_pdf_bytes)
    response = client.post(
        f"/api/resume/{thread_id}",
        json={"human_analyst_feedback": "Focus more on section 3."},
    )
    assert response.status_code == 200

    config = {"configurable": {"thread_id": thread_id}}
    final_state = quiz_agent.graph.get_state(config).values
    assert final_state["human_analyst_feedback"] == "Focus more on section 3."


def test_resume_defaults_to_approved_message_when_no_feedback_given(
    client, patch_llm, patch_qdrant_upsert, fake_vector_store, sample_pdf_bytes
):
    patch_llm(full_llm_responses())

    thread_id = _upload(client, sample_pdf_bytes)
    response = client.post(f"/api/resume/{thread_id}", json={"human_analyst_feedback": None})
    assert response.status_code == 200

    config = {"configurable": {"thread_id": thread_id}}
    final_state = quiz_agent.graph.get_state(config).values
    assert final_state["human_analyst_feedback"] == "Approved as presented."
