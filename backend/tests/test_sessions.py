import uuid

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Feedback, GradingJob, Question, User
from app.security import hash_password
from app.tasks.grading import grade_answer_task


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
def test_submitting_an_answer_queues_a_grading_job(
    client: TestClient,
    auth_headers: dict[str, str],
    questions: list[Question],
    fake_queue,  # noqa: ANN001
) -> None:
    session = _start_session(client, auth_headers)
    question_id = session["questions"][0]["id"]

    response = client.post(
        f"/sessions/{session['id']}/answers",
        headers=auth_headers,
        json={"questionId": question_id, "content": "A thoughtful answer " * 20},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["questionId"] == question_id
    assert body["id"]

    assert len(fake_queue.calls) == 1
    _, args, _ = fake_queue.calls[0]
    assert args == (body["id"],)


def test_grading_task_writes_feedback(
    client: TestClient,
    db: Session,
    auth_headers: dict[str, str],
    questions: list[Question],
    task_db,  # noqa: ANN001
) -> None:
    session = _start_session(client, auth_headers)
    job_id = client.post(
        f"/sessions/{session['id']}/answers",
        headers=auth_headers,
        json={"questionId": session["questions"][0]["id"], "content": "A detailed answer " * 30},
    ).json()["id"]

    grade_answer_task(job_id)

    job = db.get(GradingJob, uuid.UUID(job_id))
    assert job.status == "succeeded"
    assert job.attempts == 1

    result = client.get(f"/jobs/{job_id}", headers=auth_headers).json()
    assert result["status"] == "succeeded"
    assert len(result["feedback"]["scores"]) == 4


def test_grading_task_is_idempotent(
    client: TestClient,
    db: Session,
    auth_headers: dict[str, str],
    questions: list[Question],
    task_db,  # noqa: ANN001
) -> None:
    session = _start_session(client, auth_headers)
    job_id = client.post(
        f"/sessions/{session['id']}/answers",
        headers=auth_headers,
        json={"questionId": session["questions"][0]["id"], "content": "An answer " * 30},
    ).json()["id"]

    grade_answer_task(job_id)
    grade_answer_task(job_id)

    job = db.get(GradingJob, uuid.UUID(job_id))
    feedback_count = db.execute(
        select(func.count()).select_from(Feedback).where(Feedback.answer_id == job.answer_id)
    ).scalar_one()

    assert feedback_count == 1
    assert job.attempts == 1


def test_a_user_cannot_read_another_users_job(
    client: TestClient,
    db: Session,
    auth_headers: dict[str, str],
    questions: list[Question],
) -> None:
    session = _start_session(client, auth_headers)
    job_id = client.post(
        f"/sessions/{session['id']}/answers",
        headers=auth_headers,
        json={"questionId": session["questions"][0]["id"], "content": "Mine"},
    ).json()["id"]

    intruder = User(
        email="jobthief@example.com",
        display_name="Thief",
        password_hash=hash_password("password123"),
    )
    db.add(intruder)
    db.flush()

    token = client.post(
        "/auth/login", json={"email": intruder.email, "password": "password123"}
    ).json()["accessToken"]

    response = client.get(f"/jobs/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
def test_idempotency_key_replays_the_same_job(
    client: TestClient,
    auth_headers: dict[str, str],
    questions: list[Question],
    fake_queue,  # noqa: ANN001
) -> None:
    session = _start_session(client, auth_headers)
    question_id = session["questions"][0]["id"]
    headers = {**auth_headers, "Idempotency-Key": f"{session['id']}:{question_id}"}
    payload = {"questionId": question_id, "content": "An answer worth grading once"}

    first = client.post(f"/sessions/{session['id']}/answers", headers=headers, json=payload)
    second = client.post(f"/sessions/{session['id']}/answers", headers=headers, json=payload)

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json() == second.json()
    assert len(fake_queue.calls) == 1