from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_swagger import patch_fastapi

from .db.lifespan import lifespan
from .core.config import settings
from app.domains.auth import auth_routes
from app.domains.user import routes as user_routes

from app.core.logging import configure_logging

configure_logging()


app = FastAPI(
    app_name = settings.APP_NAME,
    lifespan = lifespan,
    docs_url=None,
)

patch_fastapi(app, docs_url="/api/docs")
cors_origins = [
    origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(user_routes.router)

@app.get("/health")
async def health():
    return {
        "status": "ok"
    }
    
@app.get("/")
def root():
    return {
        "message": "Welcome to fastapi API",
        "docs": "/api/docs",
    }