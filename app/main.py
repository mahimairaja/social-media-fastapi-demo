from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import database
from app.logging_conf import configure_logging
from app.routers.post import router as post_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await database.connect()  # setup
    yield
    await database.disconnect()  # teardown


app = FastAPI(lifespan=lifespan)

app.include_router(post_router)
