from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .db import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(Base, TimestampMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=True)
    about = Column(Text, nullable=True)

    posts = relationship('Post', back_populates='author', cascade='all, delete-orphan')
    comments = relationship('Comment', back_populates='author', cascade='all, delete-orphan')
    likes = relationship('Like', back_populates='user', cascade='all, delete-orphan')
    views = relationship(
        'ProfileView',
        back_populates='profile_owner',
        cascade='all, delete-orphan',
        foreign_keys='ProfileView.profile_owner_id',
    )


class Post(Base, TimestampMixin):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    author = relationship('User', back_populates='posts')
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    likes = relationship('Like', back_populates='post', cascade='all, delete-orphan')


class Comment(Base, TimestampMixin):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)

    post = relationship('Post', back_populates='comments')
    author = relationship('User', back_populates='comments')


class Like(Base):
    __tablename__ = 'likes'
    __table_args__ = (UniqueConstraint('post_id', 'user_id', name='uq_post_like'),)

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    post = relationship('Post', back_populates='likes')
    user = relationship('User', back_populates='likes')


class ProfileView(Base):
    __tablename__ = 'profile_views'

    id = Column(Integer, primary_key=True, index=True)
    profile_owner_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )
    viewer_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    viewer_name = Column(String(255), nullable=False)
    ip_address = Column(String(64), nullable=False)
    city = Column(String(120), nullable=True)
    region = Column(String(120), nullable=True)
    country = Column(String(120), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    profile_owner = relationship(
        'User',
        back_populates='views',
        foreign_keys=[profile_owner_id],
    )
    viewer = relationship(
        'User',
        foreign_keys=[viewer_id],
    )

