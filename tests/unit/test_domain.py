"""
test_domain.py — Testes unitários das entidades de domínio Task e User.

Foco: lógica pura de negócio sem dependências de banco ou rede.
Cada classe de teste agrupa um comportamento coeso da entidade.
"""
import pytest
from datetime import date, timedelta

from core.domain.task import Task
from core.domain.user import User


# ============================================================
# TASK — Criação
# ============================================================

class TestTaskCriacao:
    def test_cria_task_com_titulo_minimo(self):
        task = Task.create(title="Estudar Python")
        assert task.title == "Estudar Python"
        assert task.status == Task.STATUS_INCOMPLETE
        assert task.description == ""
        assert task.user_ids == []
        assert task.id is None

    def test_cria_task_com_todos_os_campos(self):
        prazo = date(2025, 12, 31)
        task = Task.create(
            title="  Tarefa Completa  ",
            description="  Descrição detalhada  ",
            status=Task.STATUS_ON_GOING,
            due_date=prazo,
            user_ids=[1, 2, 3],
        )
        assert task.title == "Tarefa Completa"      # strip aplicado
        assert task.description == "Descrição detalhada"
        assert task.status == Task.STATUS_ON_GOING
        assert task.due_date == prazo
        assert task.user_ids == [1, 2, 3]

    def test_titulo_vazio_levanta_value_error(self):
        with pytest.raises(ValueError, match="título"):
            Task.create(title="")

    def test_titulo_apenas_espacos_levanta_value_error(self):
        with pytest.raises(ValueError):
            Task.create(title="    ")

    def test_status_invalido_levanta_value_error(self):
        with pytest.raises(ValueError, match="Status inválido"):
            Task.create(title="Task", status="feito")

    def test_titulo_strip_aplicado(self):
        task = Task.create(title="  Título com espaços  ")
        assert task.title == "Título com espaços"

    def test_factory_classmethod_create(self):
        t1 = Task.create(title="A")
        t2 = Task(title="A")
        assert t1.title == t2.title


# ============================================================
# TASK — from_dict
# ============================================================

class TestTaskFromDict:
    def test_from_dict_campos_basicos(self):
        task = Task.from_dict({"title": "Minha Task", "id": 42})
        assert task.title == "Minha Task"
        assert task.id == 42

    def test_from_dict_due_date_string_iso(self):
        task = Task.from_dict({"title": "Task", "due_date": "2025-06-01"})
        assert task.due_date == date(2025, 6, 1)

    def test_from_dict_due_date_objeto_date(self):
        d = date(2025, 6, 1)
        task = Task.from_dict({"title": "Task", "due_date": d})
        assert task.due_date == d

    def test_from_dict_user_ids_lista_inteiros(self):
        task = Task.from_dict({"title": "Task", "user_ids": [1, 2, 3]})
        assert task.user_ids == [1, 2, 3]

    def test_from_dict_user_ids_invalido_levanta_erro(self):
        with pytest.raises(ValueError, match="user_ids"):
            Task.from_dict({"title": "Task", "user_ids": "nao-e-lista"})

    def test_from_dict_user_ids_ausente_retorna_lista_vazia(self):
        task = Task.from_dict({"title": "Task"})
        assert task.user_ids == []


# ============================================================
# TASK — update
# ============================================================

class TestTaskUpdate:
    def test_atualiza_titulo(self):
        task = Task.create(title="Antigo")
        task.update(title="Novo")
        assert task.title == "Novo"

    def test_atualiza_status(self):
        task = Task.create(title="Task")
        task.update(status=Task.STATUS_COMPLETE)
        assert task.status == Task.STATUS_COMPLETE

    def test_atualiza_descricao(self):
        task = Task.create(title="Task")
        task.update(description="Nova descrição")
        assert task.description == "Nova descrição"

    def test_titulo_vazio_na_atualizacao_levanta_erro(self):
        task = Task.create(title="Task")
        with pytest.raises(ValueError):
            task.update(title="")

    def test_status_invalido_na_atualizacao_levanta_erro(self):
        task = Task.create(title="Task")
        with pytest.raises(ValueError, match="Status inválido"):
            task.update(status="invalido")

    def test_atualiza_user_ids(self):
        task = Task.create(title="Task", user_ids=[1])
        task.update(user_ids=[2, 3])
        assert task.user_ids == [2, 3]

    def test_update_sem_args_nao_altera_nada(self):
        task = Task.create(title="Task", status=Task.STATUS_ON_GOING)
        task.update()
        assert task.title == "Task"
        assert task.status == Task.STATUS_ON_GOING


# ============================================================
# TASK — transições de status
# ============================================================

class TestTaskTransicoesStatus:
    def test_mark_complete(self):
        task = Task.create(title="Task")
        task.mark_complete()
        assert task.status == Task.STATUS_COMPLETE

    def test_mark_on_going(self):
        task = Task.create(title="Task")
        task.mark_on_going()
        assert task.status == Task.STATUS_ON_GOING

    def test_mark_incomplete(self):
        task = Task.create(title="Task", status=Task.STATUS_COMPLETE)
        task.mark_incomplete()
        assert task.status == Task.STATUS_INCOMPLETE

    def test_ciclo_completo_de_status(self):
        task = Task.create(title="Task")
        task.mark_on_going()
        assert task.status == Task.STATUS_ON_GOING
        task.mark_complete()
        assert task.status == Task.STATUS_COMPLETE
        task.mark_incomplete()
        assert task.status == Task.STATUS_INCOMPLETE


# ============================================================
# TASK — gerenciamento de user_ids
# ============================================================

class TestTaskUserIds:
    def test_add_user_id(self):
        task = Task.create(title="Task")
        task.add_user_id(99)
        assert 99 in task.user_ids

    def test_add_user_id_duplicado_nao_repete(self):
        task = Task.create(title="Task", user_ids=[5])
        task.add_user_id(5)
        assert task.user_ids.count(5) == 1

    def test_remove_user_id(self):
        task = Task.create(title="Task", user_ids=[1, 2, 3])
        task.remove_user_id(2)
        assert 2 not in task.user_ids
        assert 1 in task.user_ids
        assert 3 in task.user_ids

    def test_remove_user_id_inexistente_nao_levanta(self):
        task = Task.create(title="Task", user_ids=[1])
        task.remove_user_id(999)  # não deve explodir
        assert task.user_ids == [1]


# ============================================================
# TASK — is_overdue
# ============================================================

class TestTaskIsOverdue:
    def test_sem_prazo_nao_esta_vencida(self):
        task = Task.create(title="Task")
        assert task.is_overdue() is False

    def test_prazo_futuro_nao_esta_vencida(self):
        futuro = date.today() + timedelta(days=10)
        task = Task.create(title="Task", due_date=futuro)
        assert task.is_overdue() is False

    def test_prazo_passado_pendente_esta_vencida(self):
        passado = date.today() - timedelta(days=1)
        task = Task.create(title="Task", due_date=passado)
        assert task.is_overdue() is True

    def test_prazo_passado_mas_concluida_nao_esta_vencida(self):
        passado = date.today() - timedelta(days=5)
        task = Task.create(title="Task", due_date=passado, status=Task.STATUS_COMPLETE)
        assert task.is_overdue() is False

    def test_is_overdue_com_data_referencia_explicita(self):
        prazo = date(2025, 1, 10)
        task = Task.create(title="Task", due_date=prazo)
        assert task.is_overdue(today=date(2025, 1, 11)) is True
        assert task.is_overdue(today=date(2025, 1, 9)) is False


# ============================================================
# TASK — serialização
# ============================================================

class TestTaskSerializacao:
    def test_to_dict_contem_todas_as_chaves(self):
        task = Task.create(title="Test")
        d = task.to_dict()
        for chave in ["id", "title", "description", "status", "due_date", "user_ids"]:
            assert chave in d

    def test_to_dict_due_date_em_isoformat(self):
        task = Task.create(title="Test", due_date=date(2025, 3, 15))
        assert task.to_dict()["due_date"] == "2025-03-15"

    def test_to_dict_due_date_none_se_ausente(self):
        task = Task.create(title="Test")
        assert task.to_dict()["due_date"] is None

    def test_repr_contem_nome_da_classe_e_titulo(self):
        task = Task.create(title="Minha Task")
        r = repr(task)
        assert "Task" in r
        assert "Minha Task" in r


# ============================================================
# USER — Criação
# ============================================================

class TestUserCriacao:
    def test_cria_usuario_basico(self):
        user = User.create(username="alice", email="alice@example.com")
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.role == User.ROLE_USER
        assert user.task_ids == []
        assert user.id is None

    def test_cria_administrador(self):
        user = User.create(username="admin", email="admin@example.com", role=User.ROLE_ADMIN)
        assert user.role == User.ROLE_ADMIN
        assert user.is_admin() is True

    def test_cria_convidado(self):
        user = User.create(username="guest", email="g@example.com", role=User.ROLE_GUEST)
        assert user.is_guest() is True

    def test_role_invalido_levanta_value_error(self):
        with pytest.raises(ValueError, match="Role inválido"):
            User.create(username="x", email="x@x.com", role="SuperAdmin")


# ============================================================
# USER — from_dict
# ============================================================

class TestUserFromDict:
    def test_from_dict_campos_basicos(self):
        user = User.from_dict({"username": "bob", "email": "bob@test.com", "id": 7})
        assert user.username == "bob"
        assert user.id == 7

    def test_from_dict_task_ids_lista(self):
        user = User.from_dict({"username": "bob", "email": "b@b.com", "task_ids": [10, 20]})
        assert user.task_ids == [10, 20]

    def test_from_dict_task_ids_invalido_levanta_erro(self):
        with pytest.raises(ValueError, match="task_ids"):
            User.from_dict({"username": "bob", "email": "b@b.com", "task_ids": "invalido"})

    def test_from_dict_sem_task_ids_retorna_lista_vazia(self):
        user = User.from_dict({"username": "bob", "email": "b@b.com"})
        assert user.task_ids == []


# ============================================================
# USER — update
# ============================================================

class TestUserUpdate:
    def test_atualiza_username(self):
        user = User.create(username="antigo", email="a@test.com")
        user.update(username="novo")
        assert user.username == "novo"

    def test_atualiza_email(self):
        user = User.create(username="u", email="antigo@test.com")
        user.update(email="novo@test.com")
        assert user.email == "novo@test.com"

    def test_role_invalido_na_atualizacao_levanta_erro(self):
        user = User.create(username="u", email="u@test.com")
        with pytest.raises(ValueError, match="Role inválido"):
            user.update(role="SuperVip")

    def test_atualiza_task_ids(self):
        user = User.create(username="u", email="u@test.com")
        user.update(task_ids=[1, 2])
        assert user.task_ids == [1, 2]


# ============================================================
# USER — gerenciamento de task_ids
# ============================================================

class TestUserTaskIds:
    def test_add_task_id(self):
        user = User.create(username="u", email="u@test.com")
        user.add_task_id(42)
        assert 42 in user.task_ids

    def test_add_task_id_duplicado_nao_repete(self):
        user = User.create(username="u", email="u@test.com", task_ids=[42])
        user.add_task_id(42)
        assert user.task_ids.count(42) == 1

    def test_remove_task_id(self):
        user = User.create(username="u", email="u@test.com", task_ids=[1, 2, 3])
        user.remove_task_id(2)
        assert 2 not in user.task_ids
        assert 1 in user.task_ids

    def test_remove_task_id_inexistente_nao_levanta(self):
        user = User.create(username="u", email="u@test.com", task_ids=[1])
        user.remove_task_id(999)
        assert user.task_ids == [1]


# ============================================================
# USER — métodos de papel (role)
# ============================================================

class TestUserRoles:
    def test_is_admin(self):
        u = User.create(username="a", email="a@a.com", role=User.ROLE_ADMIN)
        assert u.is_admin() is True
        assert u.is_user() is False
        assert u.is_guest() is False

    def test_is_user(self):
        u = User.create(username="u", email="u@u.com", role=User.ROLE_USER)
        assert u.is_user() is True
        assert u.is_admin() is False
        assert u.is_guest() is False

    def test_is_guest(self):
        u = User.create(username="g", email="g@g.com", role=User.ROLE_GUEST)
        assert u.is_guest() is True
        assert u.is_admin() is False
        assert u.is_user() is False


# ============================================================
# USER — serialização
# ============================================================

class TestUserSerializacao:
    def test_to_dict_contem_todas_as_chaves(self):
        user = User.create(username="u", email="u@test.com")
        d = user.to_dict()
        for chave in ["id", "username", "email", "password_hash", "role", "task_ids"]:
            assert chave in d

    def test_repr_contem_nome_da_classe_e_username(self):
        user = User.create(username="carlos", email="c@c.com")
        r = repr(user)
        assert "User" in r
        assert "carlos" in r
