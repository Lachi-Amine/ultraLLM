from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_loaded_engines() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert all(count > 0 for count in body["engines"].values())


def test_chat_answers_empirical_question_and_reuses_conversation() -> None:
    with TestClient(app) as client:
        first = client.post("/v1/chat", json={"message": "What is velocity?"})
        second = client.post(
            "/v1/chat",
            json={
                "message": "Explain that further",
                "conversation_id": first.json()["conversation_id"],
            },
        )

    assert first.status_code == 200
    assert "velocity" in first.json()["message"]["content"].lower()
    assert first.json()["sources"]
    assert second.status_code == 200
    assert second.json()["conversation_id"] == first.json()["conversation_id"]
    assert second.json()["message"]["content"]


def test_chat_solves_math_and_rejects_invalid_expression() -> None:
    with TestClient(app) as client:
        valid = client.post("/v1/chat", json={"message": "solve x^2 = 4"})
        arithmetic = client.post("/v1/chat", json={"message": "2 + 2"})
        invalid = client.post("/v1/chat", json={"message": "solve not valid math"})

    assert valid.status_code == 200
    assert "[-2, 2]" in valid.json()["message"]["content"]
    assert "4.00000000000000" in arithmetic.json()["message"]["content"]
    assert invalid.status_code == 200
    assert "could not parse" in invalid.json()["message"]["content"].lower()


def test_chat_handles_greeting_and_no_match() -> None:
    with TestClient(app) as client:
        greeting = client.post("/v1/chat", json={"message": "hello"})
        wellbeing = client.post("/v1/chat", json={"message": "how are you?"})
        no_match = client.post("/v1/chat", json={"message": "zqxjv blorf nnnn"})

    assert "hello" in greeting.json()["message"]["content"].lower()
    assert "doing well" in wellbeing.json()["message"]["content"].lower()
    assert no_match.json()["warnings"] == ["no_reliable_evidence"]


def test_chat_corrects_common_science_misspellings() -> None:
    with TestClient(app) as client:
        first = client.post("/v1/chat", json={"message": "what is tempreture ?"})
        second = client.post("/v1/chat", json={"message": "what is tempurature"})

    assert "temperature" in first.json()["message"]["content"].lower()
    assert "temperature" in second.json()["message"]["content"].lower()
    assert {source["engine"] for source in first.json()["sources"]} == {"yellow"}


def test_chat_routes_domain_specific_questions_without_cross_domain_sources() -> None:
    with TestClient(app) as client:
        math = client.post("/v1/chat", json={"message": "What is a prime number?"})
        social = client.post("/v1/chat", json={"message": "What is justice?"})

    assert {source["engine"] for source in math.json()["sources"]} == {"green"}
    assert {source["engine"] for source in social.json()["sources"]} == {"red"}
