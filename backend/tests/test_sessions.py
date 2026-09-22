from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Question, User
from app.security import hash_password


def _start_session(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/sessions",
        headers=headers,
        json={"type": "technical", "difficulty": "medium", "questionCount": 2},
    )
    assert response.status_code == 201
    return response.json()


def test_creating_a_session_attaches_questions(
    client: TestClient, auth_headers: dict[str, str], questions: list[Question]
) -> None:
    body = _start_session(client, auth_headers)

    assert body["status"] == "in_progress"
    assert len(body["questions"]) == 2
    assert body["questions"][0]["type"] == "technical"


def test_sessions_require_authentication(client: TestClient, questions: list[Question]) -> None:
    response = client.post(
        "/sessions", json={"type": "technical", "difficulty": "medium", "questionCount": 1}
    )
    assert response.status_code == 401


def test_submitting_an_answer_returns_feedback(
    client: TestClient, auth_headers: dict[str, str], questions: list[Question]
) -> None:
    session = _start_session(client, auth_headers)
    question_id = session["questions"][0]["id"]

    response = client.post(
        f"/sessions/{session['id']}/answers",
        headers=auth_headers,
        json={"questionId": question_id, "content": "A thoughtful answer " * 20},
    )

    assert response.status_code == 201
    body = response.json()
    assert {s["dimension"] for s in body["scores"]} == {
        "correctness",
        "communication",
        "depth",
        "edge_cases",
    }
    assert body["strengths"]


def test_answering_the_same_question_twice_is_rejected(
    client: TestClient, auth_headers: dict[str, str], questions: list[Question]
) -> None:
    session = _start_session(client, auth_headers)
    payload = {"questionId": session["questions"][0]["id"], "content": "First answer"}

    client.post(f"/sessions/{session['id']}/answers", headers=auth_headers, json=payload)
    second = client.post(f"/sessions/{session['id']}/answers", headers=auth_headers, json=payload)

    assert second.status_code == 409


def test_a_user_cannot_read_another_users_session(
    client: TestClient,
    db: Session,
    auth_headers: dict[str, str],
    questions: list[Question],
) -> None:
    session = _start_session(client, auth_headers)

    intruder = User(
        email="intruder@example.com",
        display_name="Intruder",
        password_hash=hash_password("password123"),
    )
    db.add(intruder)
    db.flush()

    token = client.post(
        "/auth/login", json={"email": intruder.email, "password": "password123"}
    ).json()["accessToken"]

    response = client.get(
        f"/sessions/{session['id']}", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
