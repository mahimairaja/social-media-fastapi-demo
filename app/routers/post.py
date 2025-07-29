import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from app.database import comment_table, database, like_table, post_table
from app.models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from app.models.user import User
from app.security import get_current_user

router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    logger.info(f"Logging post with id: {post_id}")

    query = post_table.select().where(post_table.c.id == post_id)

    logger.debug(query)

    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating post")

    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(**data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post", response_model=List[UserPost])
async def get_all_posts():
    logger.info("Getting all posts")

    query = post_table.select()

    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating comment")

    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = {**comment.model_dump(), "user_id": current_user.id}
    query = comment_table.insert().values(**data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comment", response_model=List[Comment])
async def get_comments_for_post(post_id: int):
    logger.info("Getting comments on posts")

    query = comment_table.select().where(comment_table.c.post_id == post_id)

    logger.debug(query)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info("Getting posts and comments")

    post = await find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "post": post,
        "comments": await get_comments_for_post(post_id),
    }


@router.post("/like", response_model=PostLike, status_code=201)
async def list_post(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Liking post")

    post = await find_post(like.post_id)

    if not post:
        raise HTTPException(detail="Post not found", status_code=404)

    data = {**like.model_dump(), "user_id": current_user.id}

    query = like_table.insert().values(data)

    logger.debug(data)

    last_record_id = await database.execute(query)

    return {**data, "id": last_record_id}
