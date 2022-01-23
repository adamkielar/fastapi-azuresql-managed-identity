from fastapi import FastAPI

from app.api.api_v1.routes import api_router
from app.config import settings


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME, debug=settings.DEBUG, openapi_url=f"{settings.API_V1}/openapi.json"
    )
    application.include_router(api_router, prefix=settings.API_V1)

    return application


app = create_application()
