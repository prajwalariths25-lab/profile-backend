from typing import List, Optional, Tuple

from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session

from . import models, schemas


def create_user_if_not_exists(db: Session, name: str):
    name = (name or '').strip()
    if not name:
        name = "Anonymous"
    user = db.query(models.User).filter(models.User.name == name).first()
    if user:
        return user
    user = models.User(name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def _post_projection():
    return [
        models.Post.id,
        models.Post.title,
        models.Post.content,
        models.Post.created_at,
        models.Post.updated_at,
        models.User.name.label('author_name'),
        func.count(func.distinct(models.Like.id)).label('like_count'),
        func.count(func.distinct(models.Comment.id)).label('comment_count'),
    ]


def get_posts(db: Session) -> List[schemas.PostOut]:
    stmt = (
        select(*_post_projection())
        .join(models.User, models.Post.user_id == models.User.id)
        .outerjoin(models.Like, models.Like.post_id == models.Post.id)
        .outerjoin(models.Comment, models.Comment.post_id == models.Post.id)
        .group_by(models.Post.id, models.User.id)
        .order_by(models.Post.created_at.desc())
    )
    rows = db.execute(stmt).mappings().all()
    return [schemas.PostOut(**row) for row in rows]


def get_post_by_id(db: Session, post_id: int) -> Optional[schemas.PostOut]:
    stmt = (
        select(*_post_projection())
        .join(models.User, models.Post.user_id == models.User.id)
        .outerjoin(models.Like, models.Like.post_id == models.Post.id)
        .outerjoin(models.Comment, models.Comment.post_id == models.Post.id)
        .where(models.Post.id == post_id)
        .group_by(models.Post.id, models.User.id)
    )
    row = db.execute(stmt).mappings().first()
    return schemas.PostOut(**row) if row else None


def add_comment(db: Session, payload: schemas.CreateComment) -> Tuple[models.Comment, models.User]:
    user = create_user_if_not_exists(db, (payload.user_name or '').strip())
    comment_text = payload.text.strip()
    comment = models.Comment(
        post_id=payload.post_id,
        user_id=user.id,
        content=comment_text,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment, user


def get_comments(db: Session, post_id: int) -> List[schemas.CommentOut]:
    stmt = (
        select(
            models.Comment.id,
            models.Comment.post_id,
            models.Comment.user_id,
            models.Comment.content,
            models.Comment.created_at,
            models.User.name.label('user_name'),
        )
        .join(models.User, models.Comment.user_id == models.User.id)
        .where(models.Comment.post_id == post_id)
        .order_by(models.Comment.created_at.desc())
    )
    rows = db.execute(stmt).mappings().all()
    return [schemas.CommentOut(**row) for row in rows]


def add_like(db: Session, post_id: int, user_name: str):
    user = create_user_if_not_exists(db, (user_name or '').strip())
    existing = (
        db.query(models.Like)
        .filter(models.Like.post_id == post_id, models.Like.user_id == user.id)
        .first()
    )
    if existing:
        return existing
    like = models.Like(post_id=post_id, user_id=user.id)
    db.add(like)
    db.commit()
    db.refresh(like)
    return like


def get_likes_count(db: Session, post_id: int) -> int:
    stmt = select(func.count(models.Like.id)).where(models.Like.post_id == post_id)
    return db.execute(stmt).scalar_one()


def add_view(
    db: Session,
    *,
    profile_owner_id: int,
    viewer_name: str,
    ip_address: str,
    geo_data: Optional[dict] = None,
) -> models.ProfileView:
    geo_data = geo_data or {}
    normalized_name = (viewer_name or '').strip() or 'Anonymous'
    viewer = create_user_if_not_exists(db, normalized_name)
    view = models.ProfileView(
        profile_owner_id=profile_owner_id,
        viewer_id=viewer.id,
        viewer_name=viewer.name,
        ip_address=ip_address,
        city=geo_data.get('city'),
        region=geo_data.get('region'),
        country=geo_data.get('country'),
        latitude=geo_data.get('latitude'),
        longitude=geo_data.get('longitude'),
    )
    db.add(view)
    db.commit()
    db.refresh(view)
    return view


def recent_views(db: Session, user_id: int, limit: int = 5) -> List[schemas.ProfileViewOut]:
    stmt = (
        select(
            models.ProfileView.id,
            models.ProfileView.profile_owner_id,
            models.ProfileView.viewer_id,
            models.ProfileView.viewer_name,
            models.ProfileView.ip_address,
            models.ProfileView.city,
            models.ProfileView.region,
            models.ProfileView.country,
            models.ProfileView.latitude,
            models.ProfileView.longitude,
            models.ProfileView.created_at,
        )
        .where(models.ProfileView.profile_owner_id == user_id)
        .order_by(models.ProfileView.created_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).mappings().all()
    return [schemas.ProfileViewOut(**row) for row in rows]


def recent_activities(db: Session, user_id: int, limit: int = 8) -> List[schemas.ActivityOut]:
    comment_stmt = (
        select(
            models.Comment.id.label('activity_id'),
            literal('comment').label('activity_type'),
            models.User.name.label('viewer_name'),
            models.Post.title.label('post_title'),
            models.Comment.content.label('comment_text'),
            models.Comment.created_at.label('created_at'),
        )
        .join(models.Post, models.Comment.post_id == models.Post.id)
        .join(models.User, models.Comment.user_id == models.User.id)
        .where(models.Post.user_id == user_id)
    )

    like_stmt = (
        select(
            models.Like.id.label('activity_id'),
            literal('like').label('activity_type'),
            models.User.name.label('viewer_name'),
            models.Post.title.label('post_title'),
            literal(None).label('comment_text'),
            models.Like.created_at.label('created_at'),
        )
        .join(models.Post, models.Like.post_id == models.Post.id)
        .join(models.User, models.Like.user_id == models.User.id)
        .where(models.Post.user_id == user_id)
    )

    comment_rows = db.execute(comment_stmt).mappings().all()
    like_rows = db.execute(like_stmt).mappings().all()

    combined = comment_rows + like_rows
    combined.sort(key=lambda row: row['created_at'], reverse=True)
    combined = combined[:limit]

    activities: List[schemas.ActivityOut] = []
    for row in combined:
        if row['activity_type'] == 'comment':
            message = (
                f"{row['viewer_name']} commented \"{row['comment_text']}\" on \"{row['post_title']}\""
            )
        else:
            message = f"{row['viewer_name']} liked \"{row['post_title']}\""
        activities.append(
            schemas.ActivityOut(
                activity_id=row['activity_id'],
                activity_type=row['activity_type'],
                viewer_name=row['viewer_name'],
                post_title=row['post_title'],
                message=message,
                created_at=row['created_at'],
            )
        )

    return activities

