import logging

from passlib.context import CryptContext

from app.database import database, user_table

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"])


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
