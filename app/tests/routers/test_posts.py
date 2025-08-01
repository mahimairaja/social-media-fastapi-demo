import pytest
from httpx import AsyncClient

from app import security


async def create_post(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(
    body: str,
    post_id: int,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def like_post(
    async_client: AsyncClient,
    logged_in_token: str,
    post_id: int,
):
    response = await async_client.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("Test Post", async_client, logged_in_token)


@pytest.fixture()
async def created_comment(async_client: AsyncClient, logged_in_token: str):
    return await create_comment("Test Comment", 1, async_client, logged_in_token)


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    body = "Test Post"
    response = await async_client.post(
        "/post",
        json={"body": body, "user_id": confirmed_user["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert {"id": 1, "body": "Test Post"}.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, confirmed_user: dict, mocker
):
    mocker.patch("app.security.access_token_expiry_minutes", return_value=-1)
    token = security.create_access_token(confirmed_user["email"])

    response = await async_client.post(
        "/post",
        json={"body": "Test post"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_post_missing_data(
    async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/post",
        json={},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, logged_in_token: str, created_post: dict
):
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201


@pytest.mark.anyio
async def test_get_all_posts(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response = await async_client.get(
        "/post",
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 200

    assert response.json() == [created_post]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("new", [2, 1]),
        ("old", [1, 2]),
    ],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    await create_post("Test post 1", async_client, logged_in_token)
    await create_post("Test post 2", async_client, logged_in_token)

    response = await async_client.get("/post", params={"sorting": sorting})
    assert response.status_code == 200

    data = response.json()

    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
    async_client: AsyncClient,
    logged_in_token: str,
):
    await create_post("Test post 1", async_client, logged_in_token)
    await create_post("Test post 2", async_client, logged_in_token)

    await like_post(async_client, logged_in_token, 2)

    response = await async_client.get("/post", params={"sorting": "most_likes"})
    assert response.status_code == 200

    data = response.json()
    expected_order = [2, 1]

    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_wrong_sorting(
    async_client: AsyncClient,
):
    response = await async_client.get("/post", params={"sorting": "wrong"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
    confirmed_user: dict,
):
    body = "Test Comment"
    response = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": created_post["id"],
            "user_id": confirmed_user["id"],
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert {"id": 1, "body": "Test Comment"}.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_for_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(
        f"/post/{created_post['id']}/comment",
    )
    assert response.status_code == 200
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_empty(
    async_client: AsyncClient, created_post: dict
):
    response = await async_client.get(
        f"/post/{created_post['id']}/comment",
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(
        f"/post/{created_post['id']}",
    )
    assert response.status_code == 200
    assert response.json() == {
        "post": {**created_post, "likes": 0},
        "comments": [created_comment],
    }


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(
        "/post/2",
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}
