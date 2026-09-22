import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = (
    "postgresql+psycopg://pos_user:pos_password@localhost:5432/sistem_pos_test"
)

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSession = sessionmaker(
    bind=test_engine, autocommit=False, autoflush=False
)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    from app.core.database import Base
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    from app.services.seed import (
        seed_roles,
        seed_admin_user,
        seed_demo_products,
    )
    from app.models import Role, RoleEnum, User
    from app.services.auth_service import create_user

    with TestingSession() as db:
        seed_roles(db)
        seed_admin_user(db)
        seed_demo_products(db)
        if db.query(User).filter_by(username="kasir1").first() is None:
            kasir_role = db.query(Role).filter_by(
                name=RoleEnum.KASIR.value
            ).one()
            create_user(
                db,
                role_id=kasir_role.id,
                username="kasir1",
                password="kasir123",
                full_name="Kasir Test",
            )
            create_user(
                db,
                role_id=kasir_role.id,
                username="kasir2",
                password="kasir123",
                full_name="Kasir Dua",
            )
        db.commit()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    from app.core.database import get_db
    from app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()