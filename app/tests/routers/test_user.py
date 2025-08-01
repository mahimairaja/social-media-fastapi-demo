import pytest
from fastapi import Request
from httpx import AsyncClient


async def register_user(async_client: AsyncClient, email: str, password: str):
    return await async_client.post(
        "/register",
        json={
            "email": email,
            "password": password,
        },
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    response = await register_user(async_client, "test@mahimai.ca", "1234")

    assert response.status_code == 201
    assert "user created" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_already_exist(
    async_client: AsyncClient, registered_user: dict
):
    response = await register_user(
        async_client, registered_user["email"], registered_user["password"]
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_user_confirmation(async_client: AsyncClient, mocker):
    spy = mocker.spy(Request, "url_for")
    await register_user(async_client, "test@example.net", "1234")
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)

    assert response.status_code == 200
    assert "user confirmed" in response.json()["detail"]


@pytest.mark.anyio
async def test_user_confirmation_invalid_token(async_client: AsyncClient):
    response = await async_client.get("/confirm/invalid_token")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_user_confirmation_expired_token(async_client: AsyncClient, mocker):
    mocker.patch("app.security.confirm_token_expiry_minutes", return_value=-1)
    spy = mocker.spy(Request, "url_for")
    await register_user(async_client, "test@example.net", "1234")
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)

    assert response.status_code == 401
    assert "token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_exist(async_client: AsyncClient):
    response = await async_client.post(
        "/token",
        data={
            "username": "random@example.com",
            "password": "1234",
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post(
        "/token",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert response.status_code == 200
    assert "bearer" in response.json()["token_type"]
