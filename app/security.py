import datetime
import logging
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.database import database, user_table

logger = logging.getLogger(__name__)

SECRET_KEY = "1234"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"])


def create_credential_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def access_token_expiry_minutes():
    return 30


def confirm_token_expiry_minutes():
    return 1440


def create_access_token(email: str):
    logger.debug("Access token created", extra={"email": email})
    expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expiry_minutes()
    )
    jwt_data = {"sub": email, "exp": expiry, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirm_token(email: str):
    logger.debug("Access token created", extra={"email": email})
    expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expiry_minutes()
    )
    jwt_data = {"sub": email, "exp": expiry, "type": "confirm"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_subject_for_token_type(token: str, type: Literal["access", "confirm"]):
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=ALGORITHM)
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token has expired",
            headers={"WWW-Authenticate": "Bearer"},  # This says the token got expired
        ) from e

    except JWTError as e:
        raise create_credential_exception("Token invalid") from e

    email = payload.get("sub")
    if email is None:
        raise create_credential_exception("Token is missing the sub - Email")

    token_type = payload.get("type")
    if token_type is None or token_type != type:
        raise create_credential_exception(f"Invalid Token Type - expected {type}")

    return email


def get_password_hash(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


async def get_user(email: str):
    logger.debug("Fetching user from the database", extra={"email": email})

    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)

    if result:
        return result


async def authenticate_user(email: str, password: str):
    logger.debug("Authenticating user", extra={"email": email})

    user = await get_user(email)
    if not user:
        raise create_credential_exception("Invalid email or password")
    if not verify_password(password, user.password):
        raise create_credential_exception("Invalid email or password")
    if not user.confirmed:
        raise create_credential_exception("User has not confirmed mail")
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email = get_subject_for_token_type(token, "access")
    user = await get_user(email)
    if user is None:
        raise create_credential_exception("No user exists")

    return user
