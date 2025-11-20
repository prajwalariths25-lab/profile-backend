from sqlalchemy import select

from app import models
from app.db import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)


def run_seed():
    db = SessionLocal()
    try:
        user_stmt = select(models.User).where(models.User.name == 'Prajwal')
        user = db.execute(user_stmt).scalar_one_or_none()
        if not user:
            user = models.User(
                name='Prajwal',
                title='Product Engineer',
                about='Builder focused on analytics, data storytelling, and thoughtful UX.',
            )
            db.add(user)
            db.flush()

        posts_payload = [
            {
                'title': 'Launching my internship project',
                'content': 'Shipping the MVP today — full changelog, stack notes, and roadmap inside.',
            },
            {
                'title': 'How I solved a tricky bug',
                'content': 'Deep dive into the caching bug that broke analytics and how I fixed it.',
            },
            {
                'title': 'Building profile analytics in public',
                'content': 'Documenting the FastAPI + React stack powering this realtime dashboard.',
            },
        ]

        for post_data in posts_payload:
            exists_stmt = select(models.Post).where(
                models.Post.user_id == user.id, models.Post.title == post_data['title']
            )
            exists = db.execute(exists_stmt).scalar_one_or_none()
            if not exists:
                db.add(models.Post(user_id=user.id, **post_data))

        db.commit()
        print('Seed data inserted.')
    finally:
        db.close()


if __name__ == '__main__':
    run_seed()

