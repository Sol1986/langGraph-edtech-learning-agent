from tests._fakes import FakeDoc


def test_hint_endpoint_returns_hint_text(client, patch_llm, fake_vector_store):
    fake_vector_store._docs = [FakeDoc("relevant context", {"page_number": 4})]
    patch_llm({}, plain_content="Think about what happens when X increases.")

    response = client.post(
        "/api/hint",
        json={
            "question": "What is X?",
            "correct_answer": "42",
            "user_message": "I don't understand this one.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["hint"] == "Think about what happens when X increases."
    assert body["source_pages"] == [4]


def test_hint_is_grounded_in_retrieved_document_context(client, patch_llm, fake_vector_store):
    fake_vector_store._docs = [FakeDoc("some context", {"page_number": 1})]
    patch_llm({})

    client.post(
        "/api/hint",
        json={"question": "What is X?", "correct_answer": "42", "user_message": "help"},
    )

    retriever = fake_vector_store._last_retriever
    assert retriever is not None
    assert retriever.invoke_calls == ["What is X?"]


def test_hint_response_does_not_echo_correct_answer_verbatim(client, patch_llm, fake_vector_store):
    fake_vector_store._docs = [FakeDoc("context", {"page_number": 2})]
    patch_llm({}, plain_content="You're close -- reconsider the second factor.")

    response = client.post(
        "/api/hint",
        json={"question": "What is X?", "correct_answer": "42", "user_message": "help"},
    )

    assert "42" not in response.json()["hint"]
