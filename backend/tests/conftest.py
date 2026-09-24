import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Question, User
from app.security import hash_password

TEST_DB_NAME = "interview_test"
BASE_URL = settings.database_url.rsplit("/", 1)[0]
TEST_DATABASE_URL = f"{BASE_URL}/{TEST_DB_NAME}"

class _FakeJob:
    id = "fake-rq-job-id"


class _FakeQueue:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def enqueue(self, func, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        self.calls.append((func, args, kwargs))
        return _FakeJob()

@pytest.fixture(scope="session")
def engine() -> Generator[Engine]:
    admin = create_engine(f"{BASE_URL}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()

    test_engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(test_engine)

    yield test_engine

    test_engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Generator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def questions(db: Session) -> list[Question]:
    rows = [
        Question(type="technical", difficulty="medium", prompt=f"Technical question {i}")
        for i in range(3)
    ]
    db.add_all(rows)
    db.flush()
    return rows


@pytest.fixture
def user(db: Session) -> User:
    row = User(
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        display_name="Test User",
        password_hash=hash_password("password123"),
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def auth_headers(client: TestClient, db: Session, user: User) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": "password123"},
    )
    token = response.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}
@pytest.fixture(autouse=True)
def fake_queue(monkeypatch: pytest.MonkeyPatch) -> _FakeQueue:
    queue = _FakeQueue()
    monkeypatch.setattr("app.api.sessions.get_queue", lambda: queue)
    return queue


@pytest.fixture
def task_db(db, monkeypatch: pytest.MonkeyPatch):  # noqa: ANN001, ANN201
    """Make the worker task use the test session instead of opening its own."""

    class _NoCloseSession:
        def __init__(self, inner):  # noqa: ANN001
            self._inner = inner

        def __getattr__(self, name):  # noqa: ANN001, ANN204
            return getattr(self._inner, name)

        def close(self) -> None:
            pass

    monkeypatch.setattr("app.tasks.grading.SessionLocal", lambda: _NoCloseSession(db))
    return db