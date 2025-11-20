from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from . import models


from . import crud, schemas
from .db import get_db
from .utils import fetch_geo_details

router = APIRouter()


@router.get('/health', tags=['health'])
def health_check():
    return {'status': 'ok'}


@router.get('/posts', response_model=schemas.PostsResponse, tags=['posts'])
def list_posts(db: Session = Depends(get_db)):
    return crud.get_posts(db)


@router.get('/posts/{post_id}', response_model=schemas.PostOut, tags=['posts'])
def fetch_post(post_id: int, db: Session = Depends(get_db)):
    post = crud.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    return post


@router.post('/comments', response_model=schemas.CommentOut, tags=['comments'])
def create_comment(payload: schemas.CreateComment, db: Session = Depends(get_db)):
    comment, user = crud.add_comment(db, payload)
    return schemas.CommentOut(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        user_name=user.name,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get('/comments', response_model=schemas.CommentsResponse, tags=['comments'])
def read_comments(post_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    return crud.get_comments(db, post_id)


@router.post("/likes")
def post_like(payload: schemas.CreateLike, db: Session = Depends(get_db)):
    like = crud.add_like(db, payload.post_id, payload.user_name or "Anonymous")
    return {"status": "ok", "id": like.id}



@router.get('/likes/count', tags=['likes'])
def read_like_count(post_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    return {'post_id': post_id, 'likes': crud.get_likes_count(db, post_id)}

@router.get("/likes/has-liked")
def has_liked(
    post_id: int,
    user_name: str = Query('', alias='user_name'),
    db: Session = Depends(get_db),
):
    if not user_name:
        return {"liked": False}
    user = db.query(models.User).filter(models.User.name == user_name).first()
    if not user:
        return {"liked": False}
    
    like = db.query(models.Like).filter(
        models.Like.post_id == post_id,
        models.Like.user_id == user.id
    ).first()

    return {"liked": bool(like)}



@router.post('/track-view', response_model=schemas.ProfileViewOut, tags=['analytics'])
def track_view(payload: schemas.CreateView, request: Request, db: Session = Depends(get_db)):
    # 1. Get real IP (proxy-safe)
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip_address = xff.split(",")[0].strip()
    else:
        ip_address = request.client.host

    # 2. Fetch geo info
    geo = fetch_geo_details(ip_address) or {}

    # 3. Save in DB
    view = crud.add_view(
        db=db,
        profile_owner_id=payload.profile_owner_id,
        viewer_name=payload.user_name or "Anonymous",
        ip_address=ip_address,
        geo_data=geo,
    )

    # 4. Return response using your schema
    return schemas.ProfileViewOut(
        id=view.id,
        profile_owner_id=view.profile_owner_id,
        viewer_id=view.viewer_id,
        viewer_name=view.viewer_name,
        ip_address=view.ip_address,
        city=view.city,
        region=view.region,
        country=view.country,
        latitude=view.latitude,
        longitude=view.longitude,
        created_at=view.created_at,
    )



@router.get('/dashboard/views', response_model=schemas.ViewsResponse, tags=['analytics'])
def dashboard_views(
    user_id: int = Query(..., gt=0), limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)
):
    return crud.recent_views(db, user_id=user_id, limit=limit)


@router.get('/dashboard/activities', response_model=schemas.ActivitiesResponse, tags=['analytics'])
def dashboard_activities(
    user_id: int = Query(..., gt=0), limit: int = Query(8, ge=1, le=50), db: Session = Depends(get_db)
):
    return crud.recent_activities(db, user_id=user_id, limit=limit)

