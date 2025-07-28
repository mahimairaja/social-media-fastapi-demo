import datetime
import logging

from fastapi import HTTPException, status
from jose import jwt
from passlib.context import CryptContext

from app.database import database, user_table

logger = logging.getLogger(__name__)

SECRET_KEY = "1234"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"])


credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="could not validate credentials"
)


def access_token_expiry_minutes():
    return 30


def create_access_token(email: str):
    logger.debug("Access token created", extra={"email": email})
    expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expiry_minutes()
    )
    jwt_data = {"sub": email, "exp": expiry}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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
        raise credential_exception
    if not verify_password(password, user.password):
        raise credential_exception
    return user
