import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

os.environ["ENV_STATE"] = "test"

from app.database import database, user_table  # noqa
from app.main import app  # noqa: E402

# noqa tells to no quality assure
# E402 rule tells about import on top of the file


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=client.base_url,
    ) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "testemail@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)

    query = user_table.select().where(user_table.c.email == user_details.get("email"))
    user = await database.fetch_one(query)

    user_details["id"] = user.id

    return user_details
