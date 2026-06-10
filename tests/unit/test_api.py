"""
test_api.py — Testes de integração dos endpoints HTTP.

Usa o TestClient do FastAPI com dependency_overrides para substituir
repositórios reais por mocks, garantindo isolamento completo do banco.

Cobre:
  - Autenticação (login, logout, blacklist, expiração)
  - RBAC (acesso por papel: Administrador, Usuário, Convidado)
  - CRUD de Usuários
  - CRUD de Tarefas com paginação
  - Respostas de erro (400, 401, 403, 404, 422)
"""
import pytest
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# Autenticação — /auth/login e /auth/logout
# ============================================================

class TestAutenticacao:
    def test_login_credenciais_corretas_retorna_token(
        self, client, mock_user_repo, sample_user_db
    ):
        mock_user_repo.find_by_email.return_value = sample_user_db
        resp = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_usuario_inexistente_retorna_401(self, client, mock_user_repo):
        mock_user_repo.find_by_email.return_value = None
        resp = client.post(
            "/auth/login",
            json={"email": "naoexiste@x.com", "password": "qualquer"},
        )
        assert resp.status_code == 401

    def test_login_senha_errada_retorna_401(self, client, mock_user_repo, sample_user_db):
        mock_user_repo.find_by_email.return_value = sample_user_db
        resp = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "senha_errada"},
        )
        assert resp.status_code == 401

    def test_login_usuario_deletado_retorna_401(self, client, mock_user_repo, sample_user_db):
        sample_user_db["deleted_at"] = "2025-01-01T00:00:00"
        mock_user_repo.find_by_email.return_value = sample_user_db
        resp = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert resp.status_code == 401

    def test_logout_invalida_token(self, client, user_headers, mock_user_repo, sample_user_db):
        # Logout do token atual
        logout_resp = client.post("/auth/logout", headers=user_headers)
        assert logout_resp.status_code == 200
        assert "Logout" in logout_resp.json()["message"]

        # Token invalidado não pode mais acessar recurso protegido
        mock_user_repo.find_by_id.return_value = sample_user_db
        followup = client.get("/users/1", headers=user_headers)
        assert followup.status_code == 401

    def test_token_expirado_retorna_401(self, client, expired_token):
        headers = {"Authorization": f"Bearer {expired_token}"}
        resp = client.get("/users/1", headers=headers)
        assert resp.status_code == 401

    ##def test_sem_token_retorna_403(self, client):
    ##    resp = client.get("/users/1")
    ##    assert resp.status_code == 403

    def test_token_malformado_retorna_401(self, client):
        headers = {"Authorization": "Bearer nao.e.um.jwt.valido"}
        resp = client.get("/users/1", headers=headers)
        assert resp.status_code == 401

    def test_login_email_invalido_retorna_422(self, client):
        """Pydantic deve rejeitar email malformado antes de chegar ao serviço."""
        resp = client.post(
            "/auth/login",
            json={"email": "nao_e_email", "password": "123"},
        )
        assert resp.status_code == 422


# ============================================================
# Usuários — /users
# ============================================================

class TestEndpointsUsuarios:
    # --- POST /users ---

    def test_admin_cria_usuario_com_sucesso(
        self, client, admin_headers, mock_user_repo, mock_notifier
    ):
        mock_user_repo.find_by_email.return_value = None
        mock_user_repo.save.return_value = {
            "id": 5, "username": "novo", "email": "novo@example.com",
            "role": "Usuário", "task_ids": [], "deleted_at": None,
        }
        resp = client.post(
            "/users",
            headers=admin_headers,
            json={"username": "novo", "email": "novo@example.com",
                  "password": "abc123", "role": "Usuário"},
        )
        assert resp.status_code == 201
        assert resp.json()["username"] == "novo"

    def test_usuario_padrao_nao_pode_criar_usuario(self, client, user_headers):
        resp = client.post(
            "/users",
            headers=user_headers,
            json={"username": "x", "email": "x@x.com", "password": "x"},
        )
        assert resp.status_code == 403

    def test_convidado_nao_pode_criar_usuario(self, client, guest_headers):
        resp = client.post(
            "/users",
            headers=guest_headers,
            json={"username": "x", "email": "x@x.com", "password": "x"},
        )
        assert resp.status_code == 403

    def test_criar_usuario_email_duplicado_retorna_400(
        self, client, admin_headers, mock_user_repo
    ):
        mock_user_repo.find_by_email.return_value = {"id": 99}
        resp = client.post(
            "/users",
            headers=admin_headers,
            json={"username": "dup", "email": "dup@example.com", "password": "123"},
        )
        assert resp.status_code == 400

    def test_criar_usuario_payload_incompleto_retorna_422(self, client, admin_headers):
        resp = client.post("/users", headers=admin_headers, json={"username": "sem_email"})
        assert resp.status_code == 422

    # --- GET /users/{id} ---

    def test_admin_obtem_dados_completos(
        self, client, admin_headers, mock_user_repo, sample_user_db
    ):
        mock_user_repo.find_by_id.return_value = sample_user_db
        resp = client.get("/users/1", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    def test_usuario_padrao_obtem_dados_publicos(
        self, client, user_headers, mock_user_repo, sample_user_db
    ):
        mock_user_repo.find_by_id.return_value = sample_user_db
        resp = client.get("/users/1", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "username" in data
        assert "email" in data

    def test_usuario_nao_encontrado_retorna_404(
        self, client, admin_headers, mock_user_repo
    ):
        mock_user_repo.find_by_id.return_value = None
        resp = client.get("/users/9999", headers=admin_headers)
        assert resp.status_code == 404

    # --- PUT /users/{id} ---

    def test_admin_atualiza_usuario(
        self, client, admin_headers, mock_user_repo, sample_user_db
    ):
        mock_user_repo.find_by_id.return_value = sample_user_db
        mock_user_repo.save.return_value = {**sample_user_db, "username": "updated"}
        resp = client.put("/users/1", headers=admin_headers, json={"username": "updated"})
        assert resp.status_code == 200

    def test_nao_admin_nao_pode_atualizar_usuario(self, client, user_headers):
        resp = client.put("/users/1", headers=user_headers, json={"username": "x"})
        assert resp.status_code == 403

    def test_atualizar_usuario_inexistente_retorna_400(
        self, client, admin_headers, mock_user_repo
    ):
        mock_user_repo.find_by_id.return_value = None
        resp = client.put("/users/9999", headers=admin_headers, json={"username": "x"})
        assert resp.status_code == 400

    # --- DELETE /users/{id} ---

    def test_admin_deleta_usuario(
        self, client, admin_headers, mock_user_repo, mock_notifier, sample_user_db
    ):
        mock_user_repo.find_by_id.return_value = sample_user_db
        mock_user_repo.delete.return_value = True
        resp = client.delete("/users/1", headers=admin_headers)
        assert resp.status_code == 200

    def test_nao_admin_nao_pode_deletar_usuario(self, client, user_headers):
        resp = client.delete("/users/1", headers=user_headers)
        assert resp.status_code == 403

    def test_deletar_usuario_inexistente_retorna_404(
        self, client, admin_headers, mock_user_repo
    ):
        mock_user_repo.find_by_id.return_value = None
        resp = client.delete("/users/9999", headers=admin_headers)
        assert resp.status_code == 404


# ============================================================
# Tarefas — /tasks
# ============================================================

class TestEndpointsTarefas:
    # --- POST /tasks ---

    def test_usuario_padrao_cria_task(
        self, client, user_headers, mock_task_repo, mock_user_repo,
        mock_notifier, sample_task_db, sample_user_db
    ):
        mock_user_repo.find_by_id.return_value = sample_user_db
        mock_task_repo.save.return_value = sample_task_db
        mock_user_repo.save.return_value = sample_user_db

        resp = client.post(
            "/tasks",
            headers=user_headers,
            json={"title": "Tarefa de Teste", "user_ids": [1]},
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Tarefa de Teste"

    def test_admin_cria_task(
        self, client, admin_headers, mock_task_repo, mock_user_repo,
        mock_notifier, sample_task_db, sample_user_db
    ):
        mock_user_repo.find_by_id.return_value = sample_user_db
        mock_task_repo.save.return_value = sample_task_db
        mock_user_repo.save.return_value = sample_user_db

        resp = client.post(
            "/tasks",
            headers=admin_headers,
            json={"title": "Task do Admin", "user_ids": [1]},
        )
        assert resp.status_code == 201

    def test_convidado_nao_pode_criar_task(self, client, guest_headers):
        resp = client.post("/tasks", headers=guest_headers, json={"title": "Task"})
        assert resp.status_code == 403

    ##def test_sem_token_nao_pode_criar_task(self, client):
    ##    resp = client.post("/tasks", json={"title": "Task"})
    ##    assert resp.status_code == 403

    def test_usuario_associado_inexistente_retorna_400(
        self, client, user_headers, mock_user_repo
    ):
        mock_user_repo.find_by_id.return_value = None
        resp = client.post(
            "/tasks",
            headers=user_headers,
            json={"title": "Task", "user_ids": [9999]},
        )
        assert resp.status_code == 400

    def test_cria_task_com_prazo(
        self, client, user_headers, mock_task_repo, mock_user_repo,
        mock_notifier, sample_task_db, sample_user_db
    ):
        task_com_prazo = {**sample_task_db, "due_date": "2025-12-31"}
        mock_user_repo.find_by_id.return_value = sample_user_db
        mock_task_repo.save.return_value = task_com_prazo
        mock_user_repo.save.return_value = sample_user_db

        resp = client.post(
            "/tasks",
            headers=user_headers,
            json={"title": "Task com Prazo", "due_date": "2025-12-31", "user_ids": [1]},
        )
        assert resp.status_code == 201

    def test_cria_task_payload_sem_titulo_retorna_422(self, client, user_headers):
        resp = client.post("/tasks", headers=user_headers, json={"description": "sem titulo"})
        assert resp.status_code == 422

    # --- GET /tasks/{id} ---

    def test_obter_task_existente(
        self, client, user_headers, mock_task_repo, sample_task_db
    ):
        mock_task_repo.find_by_id.return_value = sample_task_db
        resp = client.get("/tasks/1", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_obter_task_inexistente_retorna_404(
        self, client, user_headers, mock_task_repo
    ):
        mock_task_repo.find_by_id.return_value = None
        resp = client.get("/tasks/9999", headers=user_headers)
        assert resp.status_code == 404

    def test_convidado_pode_ver_task(
        self, client, guest_headers, mock_task_repo, sample_task_db
    ):
        """Convidado autenticado pode visualizar tarefas (apenas leitura)."""
        mock_task_repo.find_by_id.return_value = sample_task_db
        resp = client.get("/tasks/1", headers=guest_headers)
        assert resp.status_code == 200

    # --- GET /tasks?assignedTo={userId} ---

    def test_listar_tasks_por_usuario(
        self, client, user_headers, mock_task_repo, sample_task_db
    ):
        mock_task_repo.find_by_user_id.return_value = [sample_task_db]
        resp = client.get("/tasks?assignedTo=1", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_listar_tasks_sem_assignedTo_retorna_422(self, client, user_headers):
        """assignedTo é obrigatório no endpoint de listagem."""
        resp = client.get("/tasks", headers=user_headers)
        assert resp.status_code == 422

    def test_listar_tasks_com_paginacao(
        self, client, user_headers, mock_task_repo
    ):
        mock_task_repo.find_by_user_id.return_value = []
        resp = client.get("/tasks?assignedTo=1&skip=0&limit=5", headers=user_headers)
        assert resp.status_code == 200

    #def test_listar_tasks_sem_autenticacao_retorna_403(self, client):
    #    resp = client.get("/tasks?assignedTo=1")
    #    assert resp.status_code == 403

    # --- PUT /tasks/{id} ---

    def test_atualiza_status_da_task(
        self, client, user_headers, mock_task_repo, mock_notifier, sample_task_db
    ):
        mock_task_repo.find_by_id.return_value = sample_task_db
        atualizada = {**sample_task_db, "status": "concluída"}
        mock_task_repo.save.return_value = atualizada

        resp = client.put("/tasks/1", headers=user_headers, json={"status": "concluída"})
        assert resp.status_code == 200

    def test_atualiza_titulo_da_task(
        self, client, user_headers, mock_task_repo, mock_notifier, sample_task_db
    ):
        mock_task_repo.find_by_id.return_value = sample_task_db
        atualizada = {**sample_task_db, "title": "Novo Título"}
        mock_task_repo.save.return_value = atualizada

        resp = client.put("/tasks/1", headers=user_headers, json={"title": "Novo Título"})
        assert resp.status_code == 200

    def test_convidado_nao_pode_atualizar_task(self, client, guest_headers):
        resp = client.put("/tasks/1", headers=guest_headers, json={"title": "x"})
        assert resp.status_code == 403

    def test_atualizar_task_inexistente_retorna_400(
        self, client, user_headers, mock_task_repo
    ):
        """update_task captura KeyError e retorna 400 (comportamento atual da API)."""
        mock_task_repo.find_by_id.return_value = None
        resp = client.put("/tasks/9999", headers=user_headers, json={"title": "x"})
        assert resp.status_code == 400

    # --- DELETE /tasks/{id} ---

    def test_usuario_deleta_task(
        self, client, user_headers, mock_task_repo, mock_user_repo,
        mock_notifier, sample_task_db, sample_user_db
    ):
        mock_task_repo.find_by_id.return_value = sample_task_db
        mock_user_repo.find_by_id.return_value = sample_user_db
        mock_user_repo.save.return_value = sample_user_db
        mock_task_repo.delete.return_value = True

        resp = client.delete("/tasks/1", headers=user_headers)
        assert resp.status_code == 200

    def test_convidado_nao_pode_deletar_task(self, client, guest_headers):
        resp = client.delete("/tasks/1", headers=guest_headers)
        assert resp.status_code == 403

    def test_deletar_task_inexistente_retorna_404(
        self, client, user_headers, mock_task_repo
    ):
        mock_task_repo.find_by_id.return_value = None
        resp = client.delete("/tasks/9999", headers=user_headers)
        assert resp.status_code == 404


# ============================================================
# RBAC — tabela de permissões consolidada
# ============================================================

class TestRBAC:
    """Verifica sistematicamente as regras de controle de acesso por papel."""

    @pytest.mark.parametrize("headers_fixture,expected", [
        ("admin_headers", 201),
        ("user_headers", 403),
        ("guest_headers", 403),
    ])
    def test_criar_usuario_por_papel(self, request, client, mock_user_repo, mock_notifier, headers_fixture, expected):
        mock_user_repo.find_by_email.return_value = None
        mock_user_repo.save.return_value = {
            "id": 1, "username": "n", "email": "n@n.com",
            "role": "Usuário", "task_ids": [], "deleted_at": None,
        }
        headers = request.getfixturevalue(headers_fixture)
        resp = client.post(
            "/users",
            headers=headers,
            json={"username": "n", "email": "n@n.com", "password": "123"},
        )
        assert resp.status_code == expected

    @pytest.mark.parametrize("headers_fixture,expected", [
        ("admin_headers", 200),
        ("user_headers", 403),
        ("guest_headers", 403),
    ])
    def test_deletar_usuario_por_papel(
        self, request, client, mock_user_repo, mock_notifier, headers_fixture, expected
    ):
        mock_user_repo.find_by_id.return_value = {
            "id": 1, "username": "x", "email": "x@x.com",
            "role": "Usuário", "task_ids": [], "deleted_at": None,
        }
        mock_user_repo.delete.return_value = True
        headers = request.getfixturevalue(headers_fixture)
        resp = client.delete("/users/1", headers=headers)
        assert resp.status_code == expected
