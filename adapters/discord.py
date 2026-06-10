import requests
from core.ports import NotificationPort

import os
import requests

class DiscordNotifierAdapter(NotificationPort):
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK")

    def _send(self, message: str):
        if not self.webhook_url:
            print("⚠️ [Aviso] Webhook não configurado. Notificação ignorada.")
            return

        payload = {"content": message}
        try:
            requests.post(self.webhook_url, json=payload)
        except Exception as e:
            print(f"Erro ao enviar para Discord: {e}")

    def notify_user_created(self, username: str, email: str) -> None:
        self._send(f"✅ **Novo usuário criado!**\n👤 Nome: {username}\n📧 Email: {email}")

    def notify_user_deleted(self, username: str) -> None:
        self._send(f"🗑️ **Usuário removido!**\n👤 Nome: {username}")

    def notify_task_created(self, title: str, status: str) -> None:
        self._send(f"📋 **Nova tarefa criada!**\n📌 Título: {title}\n🔄 Status: {status}")

    def notify_task_updated(self, title: str, status: str) -> None:
        self._send(f"✏️ **Tarefa atualizada!**\n📌 Título: {title}\n🔄 Status: {status}")

    def notify_task_deleted(self, title: str) -> None:
        self._send(f"🗑️ **Tarefa removida!**\n📌 Título: {title}")