from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    author_name: str = Field(..., description='Name of the author')
    like_count: int
    comment_count: int


class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    user_name: str
    content: str
    created_at: datetime


class CreateComment(BaseModel):
    post_id: int
    user_name: Optional[str] = None
    text: str


class CreateLike(BaseModel):
    post_id: int
    user_name: Optional[str] = None


class CreateView(BaseModel):
    profile_owner_id: int
    user_name: Optional[str] = None


class ProfileViewOut(BaseModel):
    id: int
    profile_owner_id: int
    viewer_id: Optional[int] = None
    viewer_name: str
    ip_address: str
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime


class ActivityOut(BaseModel):
    activity_id: int
    activity_type: str
    viewer_name: str
    post_title: str
    message: str
    created_at: datetime


PostsResponse = List[PostOut]
CommentsResponse = List[CommentOut]
ViewsResponse = List[ProfileViewOut]
ActivitiesResponse = List[ActivityOut]

