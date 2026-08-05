from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.paths import STATIC_DIR
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import admin, personality, relationship
from app.seed.personality_placeholders import seed_personality_questions, seed_personality_results


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_personality_questions(db)
        seed_personality_results(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="MBTI Platform",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(personality.router)
app.include_router(admin.router)
app.include_router(relationship.router)


@app.get("/")
def root():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/personality", status_code=303)
