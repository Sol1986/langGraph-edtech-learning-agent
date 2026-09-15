def test_summary_endpoint_matches_compute_summary(client):
    payload = {
        "results": [
            {"question": "Q1", "topic": "A", "first_attempt_correct": True},
            {"question": "Q2", "topic": "B", "first_attempt_correct": False},
        ]
    }

    response = client.post("/api/summary", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["correct_first_attempt"] == 1
    assert body["passed"] is False
    assert body["wrong_questions"] == [
        {"question": "Q2", "topic": "B", "first_attempt_correct": False}
    ]
    assert body["topics_to_focus"] == ["B"]
    assert body["topics_understood"] == ["A"]


def test_summary_endpoint_handles_empty_results(client):
    response = client.post("/api/summary", json={"results": []})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["passed"] is False
