import os

from passlib.context import CryptContext

ADMIN_USERNAME = "test-admin"
ADMIN_PASSWORD = "test-admin-parol-2026"

# Testlarda bcrypt narxini minimalga tushiramiz (hash formati bir xil qoladi).
_test_pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-a-placeholder")
os.environ.setdefault("DEBUG", "true")
os.environ["REFERRAL_REQUIRED_COMPLETIONS"] = "2"
os.environ.setdefault("ADMIN_USERNAME", ADMIN_USERNAME)
os.environ.setdefault("ADMIN_PASSWORD", ADMIN_PASSWORD)
os.environ.setdefault("ADMIN_PASSWORD_HASH", _test_pwd_context.hash(ADMIN_PASSWORD))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, session_scope
from app.main import app
from app.routers import admin
from app.seed.personality_placeholders import seed_personality_questions, seed_personality_results


@pytest.fixture(autouse=True)
def reset_login_rate_limit():
    """Limiter hisobi butun sessiya boʻyicha umumiy — har test oʻz byudjeti bilan boshlansin."""
    admin.login_limiter.reset()
    yield
    admin.login_limiter.reset()


@pytest.fixture()
def client():
    os.environ["DATABASE_URL"] = "sqlite://"
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_personality_questions(db)
    seed_personality_results(db)
    db.close()

    def override_get_db():
        yield from session_scope(TestingSessionLocal)

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.testing_session_factory = TestingSessionLocal  # type: ignore[attr-defined]
        yield test_client
    app.dependency_overrides.clear()
