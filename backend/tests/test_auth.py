from fastapi.testclient import TestClient

from app.models import User


def test_register_returns_a_token_and_never_the_hash(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "password": "password123",
            "displayName": "New User",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["role"] == "user"
    assert body["accessToken"]
    assert "passwordHash" not in body["user"]
    assert "password_hash" not in str(body)


def test_register_rejects_a_duplicate_email(client: TestClient, user: User) -> None:
    response = client.post(
        "/auth/register",
        json={"email": user.email, "password": "password123", "displayName": "Copy"},
    )
    assert response.status_code == 409


def test_register_rejects_a_short_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "abc", "displayName": "Short"},
    )
    assert response.status_code == 422


def test_login_failures_are_indistinguishable(client: TestClient, user: User) -> None:
    wrong = client.post("/auth/login", json={"email": user.email, "password": "nope"})
    missing = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "password123"}
    )

    assert wrong.status_code == 401
    assert missing.status_code == 401
    assert wrong.json() == missing.json()


def test_login_sets_an_httponly_refresh_cookie(client: TestClient, user: User) -> None:
    response = client.post("/auth/login", json={"email": user.email, "password": "password123"})

    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "refresh_token=" in cookie
    assert "HttpOnly" in cookie


def test_me_requires_authentication(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_me_rejects_a_forged_token(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_me_returns_the_current_user(
    client: TestClient, user: User, auth_headers: dict[str, str]
) -> None:
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == user.email
