"""
test_services.py — Testes unitários da camada de serviço.

Repositórios e notificadores são substituídos por MagicMock para que
os testes sejam rápidos, determinísticos e isolados de qualquer banco.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import jwt
from passlib.context import CryptContext

from core.service import UserService, TaskService, SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Fixtures locais
# ---------------------------------------------------------------------------

@pytest.fixture
def user_repo():
    return MagicMock()


@pytest.fixture
def task_repo():
    return MagicMock()


@pytest.fixture
def notifier():
    return MagicMock()


@pytest.fixture
def user_svc(user_repo, notifier):
    return UserService(user_repo, notifier)


@pytest.fixture
def task_svc(task_repo, user_repo, notifier):
    return TaskService(task_repo, user_repo, notifier)


@pytest.fixture
def db_user():
    return {
        "id": 1,
        "username": "joao",
        "email": "joao@example.com",
        "password_hash": pwd_context.hash("senha123"),
        "role": "Usuário",
        "task_ids": [],
        "deleted_at": None,
    }


@pytest.fixture
def db_task():
    return {
        "id": 1,
        "title": "Implementar feature X",
        "description": "Detalhes da feature",
        "status": "pendente",
        "due_date": None,
        "user_ids": [1],
    }


# ============================================================
# UserService — create_user
# ============================================================

class TestUserServiceCriarUsuario:
    def test_cria_usuario_com_sucesso(self, user_svc, user_repo, notifier):
        user_repo.find_by_email.return_value = None
        user_repo.save.return_value = {
            "id": 1, "username": "maria", "email": "maria@example.com",
            "role": "Usuário", "task_ids": [], "deleted_at": None,
        }
        resultado = user_svc.create_user({
            "username": "maria", "email": "maria@example.com",
            "password": "senha123", "role": "Usuário",
        })
        assert resultado["username"] == "maria"
        notifier.notify_user_created.assert_called_once_with("maria", "maria@example.com")

    def test_email_duplicado_levanta_value_error(self, user_svc, user_repo):
        user_repo.find_by_email.return_value = {"id": 5}
        with pytest.raises(ValueError, match="Email já cadastrado"):
            user_svc.create_user({"username": "x", "email": "dup@x.com", "password": "123"})

    def test_senha_e_armazenada_como_hash(self, user_svc, user_repo, notifier):
        user_repo.find_by_email.return_value = None
        capturado = {}

        def salvar(data):
            capturado.update(data)
            return {**data, "id": 99}

        user_repo.save.side_effect = salvar
        user_svc.create_user({"username": "u", "email": "u@u.com", "password": "minha_senha"})

        hash_salvo = capturado.get("password_hash", "")
        assert hash_salvo != "minha_senha"
        assert pwd_context.verify("minha_senha", hash_salvo)

    def test_notificador_nao_chamado_em_email_duplicado(self, user_svc, user_repo, notifier):
        user_repo.find_by_email.return_value = {"id": 1}
        with pytest.raises(ValueError):
            user_svc.create_user({"username": "x", "email": "dup@x.com", "password": "123"})
        notifier.notify_user_created.assert_not_called()


# ============================================================
# UserService — get_user
# ============================================================

class TestUserServiceObterUsuario:
    def test_retorna_usuario_existente(self, user_svc, user_repo, db_user):
        user_repo.find_by_id.return_value = db_user
        resultado = user_svc.get_user(1)
        assert resultado["id"] == 1
        assert resultado["username"] == "joao"

    def test_usuario_inexistente_levanta_key_error(self, user_svc, user_repo):
        user_repo.find_by_id.return_value = None
        with pytest.raises(KeyError, match="não encontrado"):
            user_svc.get_user(999)

    def test_usuario_soft_deleted_levanta_key_error(self, user_svc, user_repo, db_user):
        db_user["deleted_at"] = "2025-01-01T00:00:00"
        user_repo.find_by_id.return_value = db_user
        with pytest.raises(KeyError, match="não encontrado"):
            user_svc.get_user(1)


# ============================================================
# UserService — update_user
# ============================================================

class TestUserServiceAtualizarUsuario:
    def test_atualiza_com_sucesso(self, user_svc, user_repo, db_user):
        user_repo.find_by_id.return_value = db_user
        esperado = {**db_user, "username": "joao_updated"}
        user_repo.save.return_value = esperado

        resultado = user_svc.update_user(1, {"username": "joao_updated"})
        assert resultado["username"] == "joao_updated"
        user_repo.save.assert_called_once()

    def test_usuario_inexistente_levanta_key_error(self, user_svc, user_repo):
        user_repo.find_by_id.return_value = None
        with pytest.raises(KeyError):
            user_svc.update_user(999, {"username": "novo"})


# ============================================================
# UserService — delete_user
# ============================================================

class TestUserServiceDeletarUsuario:
    def test_deleta_com_sucesso(self, user_svc, user_repo, notifier, db_user):
        user_repo.find_by_id.return_value = db_user
        user_repo.delete.return_value = True

        resultado = user_svc.delete_user(1)
        assert "removido" in resultado["message"].lower()
        notifier.notify_user_deleted.assert_called_once_with("joao")

    def test_usuario_inexistente_levanta_key_error(self, user_svc, user_repo):
        user_repo.find_by_id.return_value = None
        with pytest.raises(KeyError):
            user_svc.delete_user(999)

    def test_notificador_chamado_com_username_correto(self, user_svc, user_repo, notifier, db_user):
        user_repo.find_by_id.return_value = db_user
        user_repo.delete.return_value = True
        user_svc.delete_user(1)
        notifier.notify_user_deleted.assert_called_with("joao")


# ============================================================
# UserService — login
# ============================================================

class TestUserServiceLogin:
    def test_login_com_sucesso(self, user_svc, user_repo, db_user):
        user_repo.find_by_email.return_value = db_user
        resultado = user_svc.login({"email": "joao@example.com", "password": "senha123"})
        assert "access_token" in resultado
        assert resultado["token_type"] == "bearer"

    def test_email_inexistente_levanta_value_error(self, user_svc, user_repo):
        user_repo.find_by_email.return_value = None
        with pytest.raises(ValueError, match="Credenciais inválidas"):
            user_svc.login({"email": "naoexiste@x.com", "password": "123"})

    def test_senha_errada_levanta_value_error(self, user_svc, user_repo, db_user):
        user_repo.find_by_email.return_value = db_user
        with pytest.raises(ValueError, match="Credenciais inválidas"):
            user_svc.login({"email": "joao@example.com", "password": "senha_errada"})

    def test_usuario_deletado_levanta_value_error(self, user_svc, user_repo, db_user):
        db_user["deleted_at"] = "2025-01-01T00:00:00"
        user_repo.find_by_email.return_value = db_user
        with pytest.raises(ValueError, match="Credenciais inválidas"):
            user_svc.login({"email": "joao@example.com", "password": "senha123"})

    def test_token_contem_payload_correto(self, user_svc, user_repo, db_user):
        user_repo.find_by_email.return_value = db_user
        resultado = user_svc.login({"email": "joao@example.com", "password": "senha123"})
        payload = jwt.decode(resultado["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["email"] == "joao@example.com"
        assert payload["role"] == "Usuário"
        assert payload["sub"] == "1"

    def test_token_expiracao_no_futuro(self, user_svc, user_repo, db_user):
        user_repo.find_by_email.return_value = db_user
        resultado = user_svc.login({"email": "joao@example.com", "password": "senha123"})
        payload = jwt.decode(resultado["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
        agora = datetime.now(timezone.utc).timestamp()
        assert payload["exp"] > agora


# ============================================================
# TaskService — create_task
# ============================================================

class TestTaskServiceCriarTask:
    def test_cria_task_com_sucesso(self, task_svc, task_repo, user_repo, notifier, db_user, db_task):
        user_repo.find_by_id.return_value = db_user
        task_repo.save.return_value = db_task
        user_repo.save.return_value = db_user

        resultado = task_svc.create_task({"title": "Implementar feature X", "user_ids": [1]})
        assert resultado["title"] == "Implementar feature X"
        notifier.notify_task_created.assert_called_once()

    def test_usuario_associado_inexistente_levanta_value_error(self, task_svc, user_repo):
        user_repo.find_by_id.return_value = None
        with pytest.raises(ValueError, match="não existe"):
            task_svc.create_task({"title": "Task", "user_ids": [9999]})

    def test_cria_task_sem_usuarios_associados(self, task_svc, task_repo, user_repo, notifier):
        task_sem_users = {
            "id": 2, "title": "Task Simples", "description": "",
            "status": "pendente", "due_date": None, "user_ids": [],
        }
        task_repo.save.return_value = task_sem_users

        resultado = task_svc.create_task({"title": "Task Simples", "user_ids": []})
        assert resultado["user_ids"] == []
        notifier.notify_task_created.assert_called_once()

    def test_usuario_atualizado_com_task_id_apos_criacao(self, task_svc, task_repo, user_repo, notifier, db_user, db_task):
        """Verifica que o user_repo.save é chamado para associar o task_id ao usuário."""
        user_repo.find_by_id.return_value = db_user
        task_repo.save.return_value = db_task
        user_repo.save.return_value = db_user

        task_svc.create_task({"title": "Task", "user_ids": [1]})
        user_repo.save.assert_called()


# ============================================================
# TaskService — get_task
# ============================================================

class TestTaskServiceObterTask:
    def test_retorna_task_existente(self, task_svc, task_repo, db_task):
        task_repo.find_by_id.return_value = db_task
        resultado = task_svc.get_task(1)
        assert resultado["id"] == 1

    def test_task_inexistente_levanta_key_error(self, task_svc, task_repo):
        task_repo.find_by_id.return_value = None
        with pytest.raises(KeyError, match="não encontrada"):
            task_svc.get_task(9999)


# ============================================================
# TaskService — update_task
# ============================================================

class TestTaskServiceAtualizarTask:
    def test_atualiza_titulo_e_status(self, task_svc, task_repo, notifier, db_task):
        task_repo.find_by_id.return_value = db_task
        atualizada = {**db_task, "title": "Feature Atualizada", "status": "em andamento"}
        task_repo.save.return_value = atualizada

        resultado = task_svc.update_task(1, {"title": "Feature Atualizada", "status": "em andamento"})
        assert resultado["title"] == "Feature Atualizada"
        assert resultado["status"] == "em andamento"
        notifier.notify_task_updated.assert_called_once()

    def test_task_inexistente_levanta_key_error(self, task_svc, task_repo):
        task_repo.find_by_id.return_value = None
        with pytest.raises(KeyError):
            task_svc.update_task(9999, {"title": "x"})

    def test_atualiza_due_date_como_string(self, task_svc, task_repo, notifier, db_task):
        task_repo.find_by_id.return_value = db_task
        task_repo.save.return_value = {**db_task, "due_date": "2025-12-31"}
        resultado = task_svc.update_task(1, {"due_date": "2025-12-31"})
        assert resultado["due_date"] == "2025-12-31"


# ============================================================
# TaskService — delete_task
# ============================================================

class TestTaskServiceDeletarTask:
    def test_deleta_com_sucesso(self, task_svc, task_repo, user_repo, notifier, db_user, db_task):
        task_repo.find_by_id.return_value = db_task
        user_repo.find_by_id.return_value = db_user
        user_repo.save.return_value = db_user
        task_repo.delete.return_value = True

        resultado = task_svc.delete_task(1)
        assert "deletada" in resultado["message"].lower()
        notifier.notify_task_deleted.assert_called_once_with("Implementar feature X")

    def test_task_inexistente_levanta_key_error(self, task_svc, task_repo):
        task_repo.find_by_id.return_value = None
        with pytest.raises(KeyError):
            task_svc.delete_task(9999)

    def test_disassocia_usuarios_ao_deletar(self, task_svc, task_repo, user_repo, notifier, db_user, db_task):
        """Verifica que user_repo.save é chamado para remover o task_id do usuário."""
        task_repo.find_by_id.return_value = db_task
        user_repo.find_by_id.return_value = db_user
        user_repo.save.return_value = db_user
        task_repo.delete.return_value = True

        task_svc.delete_task(1)
        user_repo.save.assert_called()


# ============================================================
# TaskService — get_tasks_by_user
# ============================================================

class TestTaskServiceListarTasksPorUsuario:
    def test_retorna_lista_de_tasks(self, task_svc, task_repo, db_task):
        task_repo.find_by_user_id.return_value = [db_task]
        resultado = task_svc.get_tasks_by_user(1)
        assert len(resultado) == 1
        assert resultado[0]["title"] == "Implementar feature X"

    def test_retorna_lista_vazia_se_sem_tasks(self, task_svc, task_repo):
        task_repo.find_by_user_id.return_value = []
        resultado = task_svc.get_tasks_by_user(1)
        assert resultado == []

    def test_repassa_skip_e_limit_ao_repositorio(self, task_svc, task_repo):
        task_repo.find_by_user_id.return_value = []
        task_svc.get_tasks_by_user(1, skip=5, limit=20)
        task_repo.find_by_user_id.assert_called_with(1, skip=5, limit=20)
