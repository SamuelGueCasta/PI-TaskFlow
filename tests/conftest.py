"""
Configuración común para las pruebas de caja blanca de TaskFlow.

Se usa una base de datos SQLite en memoria para no tocar la base de datos
MySQL real. La dependencia get_db se sobrescribe para que todos los routers
usen la sesión de pruebas.
"""
import os

# Variables de entorno de prueba (deben existir antes de importar la app)
os.environ.setdefault("SECRET_KEY", "clave_de_prueba_taskflow")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.models import Usuario
from app.utils.security import hashear_contrasena

# Motor SQLite en memoria, compartido entre conexiones (StaticPool)
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    usuario = Usuario(
        nombreUsuario="Admin",
        apellidosUsuario="Principal",
        emailUsuario="admin@taskflow.com",
        contraseñaUsuario=hashear_contrasena("admin123"),
        rolUsuario="admin",
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


@pytest.fixture
def standard_user(db_session):
    usuario = Usuario(
        nombreUsuario="Empleado",
        apellidosUsuario="Estandar",
        emailUsuario="empleado@taskflow.com",
        contraseñaUsuario=hashear_contrasena("empleado123"),
        rolUsuario="usuario",
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


def _login(client, email, password):
    respuesta = client.post(
        "/auth/login",
        json={"emailUsuario": email, "contraseñaUsuario": password},
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    return _login(client, "admin@taskflow.com", "admin123")


@pytest.fixture
def standard_token(client, standard_user):
    return _login(client, "empleado@taskflow.com", "empleado123")


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}
