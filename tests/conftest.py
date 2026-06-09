"""
conftest.py — fixtures compartilhados entre todos os módulos de teste.

"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import jwt
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from adapters.swagger_api import app
from core.dependencies import (
    get_user_repository,
    get_task_repository,
    get_notification_port,
    blacklisted_tokens,
)
from core.service import SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id: int, email: str, role: str, *, expired: bool = False) -> str:
    """Gera um JWT válido (ou expirado) para uso nos testes de API."""
    delta = timedelta(seconds=-1) if expired else timedelta(hours=2)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": int((datetime.now(timezone.utc) + delta).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Tokens prontos
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_token() -> str:
    return _make_token(1, "admin@test.com", "Administrador")


@pytest.fixture
def user_token() -> str:
    return _make_token(2, "user@test.com", "Usuário")


@pytest.fixture
def guest_token() -> str:
    return _make_token(3, "guest@test.com", "Convidado")


@pytest.fixture
def expired_token() -> str:
    return _make_token(1, "old@test.com", "Usuário", expired=True)


@pytest.fixture
def admin_headers(admin_token) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def guest_headers(guest_token) -> dict:
    return {"Authorization": f"Bearer {guest_token}"}


# ---------------------------------------------------------------------------
# Mocks de repositórios e notificador
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_task_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_notifier() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# Client HTTP com dependências injetadas via override
# ---------------------------------------------------------------------------

@pytest.fixture
def client(mock_user_repo, mock_task_repo, mock_notifier):
    """TestClient do FastAPI com repositórios e notificador mockados."""
    blacklisted_tokens.clear()
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repo
    app.dependency_overrides[get_task_repository] = lambda: mock_task_repo
    app.dependency_overrides[get_notification_port] = lambda: mock_notifier
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    blacklisted_tokens.clear()


# ---------------------------------------------------------------------------
# Dados de exemplo
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user_db() -> dict:
    """Usuário salvo no banco (com senha hasheada)."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": pwd_context.hash("password123"),
        "role": "Usuário",
        "task_ids": [],
        "deleted_at": None,
    }


@pytest.fixture
def sample_admin_db() -> dict:
    return {
        "id": 10,
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": pwd_context.hash("admin123"),
        "role": "Administrador",
        "task_ids": [],
        "deleted_at": None,
    }


@pytest.fixture
def sample_task_db() -> dict:
    return {
        "id": 1,
        "title": "Tarefa de Teste",
        "description": "Descrição da tarefa",
        "status": "pendente",
        "due_date": None,
        "user_ids": [1],
    }
