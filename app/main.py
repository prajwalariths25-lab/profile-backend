from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .db import Base, engine
from .routes import router as api_router


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title='Profile Analytics API', version='1.0.0', docs_url='/docs')

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(api_router, prefix='/api')

    return app


app = create_app()

