from fastapi import FastAPI
from app.timekeeping.api import router as timekeeping_router
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.crm import router as crm_router
from app.routers.quoting import router as quoting_router

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(admin_router, prefix=settings.API_PREFIX)
app.include_router(crm_router, prefix=settings.API_PREFIX)
app.include_router(quoting_router, prefix=settings.API_PREFIX)
app.include_router(timekeeping_router, prefix=settings.API_PREFIX)

@app.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}
