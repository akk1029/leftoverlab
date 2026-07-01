"""Community platform schemas (FR14 / data rule 2.5)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1)


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    post_id: str
    author_id: str
    body: str
    created_at: datetime


class PostBase(BaseModel):
    title: str = Field(..., max_length=200)
    body: str = Field(..., min_length=1)
    post_type: str = Field(default="experience", pattern="^(recipe|tip|experience)$")


class PostCreate(PostBase):
    pass


class PostPublic(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    author_id: str
    created_at: datetime
    comments: list[CommentPublic] = Field(default_factory=list)
