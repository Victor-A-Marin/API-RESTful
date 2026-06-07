import requests

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1513289091788308520/weXlDoTMxmBdOO8C_EGJRXXpghaErbJVm3t4TrDKvC6lPH_1cHPvGorUsEOalzkMh9TW"

def notify_user_created(username: str, email: str) -> None:
    message = {
        "content": f"✅ **Novo usuário criado!**\n👤 Nome: {username}\n📧 Email: {email}"
    }
    requests.post(WEBHOOK_URL, json=message)

def notify_user_deleted(username: str) -> None:
    message = {
        "content": f"🗑️ **Usuário removido!**\n👤 Nome: {username}"
    }
    requests.post(WEBHOOK_URL, json=message)

def notify_task_created(title: str, status: str) -> None:
    message = {
        "content": f"📋 **Nova tarefa criada!**\n📌 Título: {title}\n🔄 Status: {status}"
    }
    requests.post(WEBHOOK_URL, json=message)

def notify_task_updated(title: str, status: str) -> None:
    message = {
        "content": f"✏️ **Tarefa atualizada!**\n📌 Título: {title}\n🔄 Status: {status}"
    }
    requests.post(WEBHOOK_URL, json=message)

def notify_task_deleted(title: str) -> None:
    message = {
        "content": f"🗑️ **Tarefa removida!**\n📌 Título: {title}"
    }
    requests.post(WEBHOOK_URL, json=message)