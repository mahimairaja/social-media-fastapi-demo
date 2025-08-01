import pytest
from jose import jwt

from app import security


@pytest.mark.anyio
async def test_access_token_expiry_minutes():
    assert 30 == security.access_token_expiry_minutes()


@pytest.mark.anyio
async def test_confirm_token_expiry_minutes():
    assert 1440 == security.confirm_token_expiry_minutes()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "type",
    [
        ("access",),
        ("confirm",),
    ],
)
async def test_access_tokens(type):
    if type == "access":
        token = security.create_access_token("123")
        assert {"sub": "123", "type": type}.items() <= jwt.decode(
            token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
        ).items()
    elif type == "confirm":
        token = security.create_confirm_token("123")
        assert {"sub": "123", "type": type}.items() <= jwt.decode(
            token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
        ).items()


@pytest.mark.anyio
@pytest.mark.parametrize("type", [("access"), ("confirm")])
async def test_create_subject_for_token_type_valid_confirmation(type):
    email = "test@email.net"
    if type == "confirm":
        token = security.create_confirm_token(email)
    elif type == "access":
        token = security.create_access_token(email)
    assert security.get_subject_for_token_type(token, type) == email


@pytest.mark.anyio
async def test_create_subject_for_token_type_expired(mocker):
    mocker.patch("app.security.access_token_expiry_minutes", return_value=-1)
    email = "test@email.net"
    token = security.create_access_token(email)

    with pytest.raises(security.HTTPException) as exec_info:
        security.get_subject_for_token_type(token, "access")

    assert "token has expired" == exec_info.value.detail


@pytest.mark.anyio
async def test_create_subject_for_token_invalid():
    token = "invalid token"

    with pytest.raises(security.HTTPException) as exec_info:
        security.get_subject_for_token_type(token, "access")

    assert "Token invalid" == exec_info.value.detail


@pytest.mark.anyio
async def test_create_subject_for_token_type_missing_sub():
    email = "test@email.net"
    token = security.create_access_token(email)
    payload = jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    )

    del payload["sub"]

    token = jwt.encode(payload, key=security.SECRET_KEY, algorithm=security.ALGORITHM)

    with pytest.raises(security.HTTPException) as exec_info:
        security.get_subject_for_token_type(token, "access")

    assert "Token is missing the sub - Email" == exec_info.value.detail


@pytest.mark.anyio
async def test_create_subject_for_token_type_wrong_type():
    email = "test@email.net"
    token = security.create_access_token(email)

    with pytest.raises(security.HTTPException) as exec_info:
        security.get_subject_for_token_type(token, "confirm")

    assert "Invalid Token Type - expected confirm" == exec_info.value.detail


@pytest.mark.anyio
async def test_hash_password():
    password = "password"
    assert security.verify_password(password, security.get_password_hash(password))


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example.com")

    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"],
        confirmed_user["password"],
    )
    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.net", "1234")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registered_user["email"], "wrong password")


@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("Some random")


@pytest.mark.anyio
async def test_get_current_user_wrong_type_token(registered_user: dict):
    token = security.create_confirm_token(registered_user["email"])

    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)
