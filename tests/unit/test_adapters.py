"""
test_adapters.py — Testes unitários do DiscordNotifierAdapter.

Verifica:
  - Todas as notificações disparam requests.post com o payload correto
  - Ausência de webhook não lança exceção
  - Falha de rede é absorvida silenciosamente (sem propagar para a aplicação)
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from adapters.discord import DiscordNotifierAdapter

FAKE_WEBHOOK = "https://discord.com/api/webhooks/123/abc"


def _adapter_com_webhook() -> DiscordNotifierAdapter:
    """Cria adaptador com webhook configurado via variável de ambiente."""
    with patch.dict(os.environ, {"DISCORD_WEBHOOK": FAKE_WEBHOOK}):
        return DiscordNotifierAdapter()


def _adapter_sem_webhook() -> DiscordNotifierAdapter:
    """Cria adaptador sem variável de ambiente configurada."""
    env = {k: v for k, v in os.environ.items() if k != "DISCORD_WEBHOOK"}
    with patch.dict(os.environ, env, clear=True):
        adapter = DiscordNotifierAdapter()
        adapter.webhook_url = None
        return adapter


# ============================================================
# Notificações enviadas quando webhook está configurado
# ============================================================

class TestDiscordEnvioComWebhook:
    def test_notify_user_created_chama_post(self):
        adapter = _adapter_com_webhook()
        with patch("requests.post") as mock_post:
            adapter.notify_user_created("alice", "alice@example.com")
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert "alice" in payload["content"]

    def test_notify_user_deleted_chama_post(self):
        adapter = _adapter_com_webhook()
        with patch("requests.post") as mock_post:
            adapter.notify_user_deleted("bob")
        mock_post.assert_called_once()

    def test_notify_task_created_chama_post(self):
        adapter = _adapter_com_webhook()
        with patch("requests.post") as mock_post:
            adapter.notify_task_created("Minha Task", "pendente")
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert "Minha Task" in payload["content"]

    def test_notify_task_updated_chama_post(self):
        adapter = _adapter_com_webhook()
        with patch("requests.post") as mock_post:
            adapter.notify_task_updated("Task X", "concluída")
        mock_post.assert_called_once()

    def test_notify_task_deleted_chama_post(self):
        adapter = _adapter_com_webhook()
        with patch("requests.post") as mock_post:
            adapter.notify_task_deleted("Task Removida")
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert "Task Removida" in payload["content"]

    def test_url_correta_no_post(self):
        adapter = _adapter_com_webhook()
        with patch("requests.post") as mock_post:
            adapter.notify_user_created("x", "x@x.com")
        url_chamada = mock_post.call_args[0][0] if mock_post.call_args[0] else mock_post.call_args.args[0]
        assert url_chamada == FAKE_WEBHOOK


# ============================================================
# Comportamento sem webhook configurado
# ============================================================

class TestDiscordSemWebhook:
    def test_notify_user_created_nao_chama_post(self):
        adapter = _adapter_sem_webhook()
        with patch("requests.post") as mock_post:
            adapter.notify_user_created("alice", "alice@example.com")
        mock_post.assert_not_called()

    def test_notify_task_created_nao_chama_post(self):
        adapter = _adapter_sem_webhook()
        with patch("requests.post") as mock_post:
            adapter.notify_task_created("Task", "pendente")
        mock_post.assert_not_called()

    def test_nenhum_metodo_levanta_excecao_sem_webhook(self):
        adapter = _adapter_sem_webhook()
        with patch("requests.post"):
            adapter.notify_user_created("u", "u@u.com")
            adapter.notify_user_deleted("u")
            adapter.notify_task_created("t", "pendente")
            adapter.notify_task_updated("t", "concluída")
            adapter.notify_task_deleted("t")
        # Nenhuma exceção deve ter sido levantada


# ============================================================
# Resiliência — falha de rede é absorvida
# ============================================================

class TestDiscordResiliencia:
    def test_exception_em_requests_post_nao_propaga(self):
        """A aplicação não pode travar por causa de uma falha de notificação."""
        adapter = _adapter_com_webhook()
        with patch("requests.post", side_effect=Exception("Connection refused")):
            # Não deve levantar exceção
            adapter.notify_task_created("Task", "pendente")

    def test_timeout_em_requests_post_nao_propaga(self):
        import requests as req_module
        adapter = _adapter_com_webhook()
        with patch("requests.post", side_effect=req_module.exceptions.Timeout()):
            adapter.notify_user_created("alice", "a@a.com")

    def test_connection_error_nao_propaga(self):
        import requests as req_module
        adapter = _adapter_com_webhook()
        with patch("requests.post", side_effect=req_module.exceptions.ConnectionError()):
            adapter.notify_task_deleted("Task")
