"""Community sharing platform routes: posts & comments (FR14)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.core.ids import next_id
from app.models.community import Comment, Post
from app.schemas.community import (
    CommentCreate,
    CommentPublic,
    PostCreate,
    PostPublic,
)

router = APIRouter(prefix="/community", tags=["community"])


@router.post("/posts", response_model=PostPublic, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: DbSession, current_user: CurrentUser) -> Post:
    post = Post(
        id=next_id(db, "P", 4),
        author_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.get("/posts", response_model=list[PostPublic])
def list_posts(
    db: DbSession,
    current_user: CurrentUser,
    post_type: str | None = Query(default=None, pattern="^(recipe|tip|experience)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Post]:
    q = db.query(Post)
    if post_type:
        q = q.filter(Post.post_type == post_type)
    return q.order_by(Post.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/posts/{post_id}", response_model=PostPublic)
def get_post(post_id: str, db: DbSession, current_user: CurrentUser) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_post(post_id: str, db: DbSession, current_user: CurrentUser) -> None:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your post.")
    db.delete(post)
    db.commit()


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentPublic,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    post_id: str, payload: CommentCreate, db: DbSession, current_user: CurrentUser
) -> Comment:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    comment = Comment(
        id=next_id(db, "CM", 4),
        post_id=post_id,
        author_id=current_user.id,
        body=payload.body,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/posts/{post_id}/comments", response_model=list[CommentPublic])
def list_comments(post_id: str, db: DbSession, current_user: CurrentUser) -> list[Comment]:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    return (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_comment(comment_id: str, db: DbSession, current_user: CurrentUser) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment.")
    db.delete(comment)
    db.commit()
