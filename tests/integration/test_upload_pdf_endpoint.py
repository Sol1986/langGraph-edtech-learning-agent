import uuid

from tests._fakes import full_llm_responses


def test_upload_pdf_rejects_non_pdf_content_type(client, sample_pdf_bytes):
    response = client.post(
        "/api/upload-pdf",
        files={"file": ("notes.txt", sample_pdf_bytes, "text/plain")},
    )
    assert response.status_code == 400


def test_upload_pdf_rejects_empty_file(client):
    response = client.post(
        "/api/upload-pdf",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422


def test_upload_pdf_happy_path_returns_thread_id_and_plan(
    client, patch_llm, patch_qdrant_upsert, sample_pdf_bytes
):
    patch_llm(full_llm_responses())

    response = client.post(
        "/api/upload-pdf",
        files={"file": ("lesson.pdf", sample_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    uuid.UUID(body["thread_id"])  # raises if not a valid UUID
    assert body["course_topic"] == "Test Topic"
    assert body["learning_plan"]
    assert body["status"] == "awaiting_approval"
