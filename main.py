import uvicorn
from fastapi import FastAPI
from database.database import MySQLUserRepository, MySQLTaskRepository
from core.dependencies import (
    get_user_repository, 
    get_task_repository, 
    get_notification_port
)
from adapters.discord import DiscordNotifierAdapter
from adapters.swagger_api import app # Supondo que app está em swagger_api

import os
import sys


# 1. Configurações e Instâncias
def check_discord_webhook():
    webhook = os.getenv("DISCORD_WEBHOOK")
    
    if not webhook:
        print("\n" + "="*50)
        print("⚠️  Webhook do Discord não detectado.")
        print("Cole a URL abaixo (ou pressione ENTER para rodar sem notificações):")
        
        user_input = input(">> ").strip()
        
        if user_input:
            os.environ["DISCORD_WEBHOOK"] = user_input
            print("✅ Webhook configurado com sucesso!")
        else:
            print("ℹ️ Rodando sem notificações Discord.")
        print("="*50 + "\n")

# Chame isso ANTES de instanciar o service
check_discord_webhook()
# 2. Injeção de dependências via Overrides do FastAPI
# O FastAPI usará essas instâncias sempre que um endpoint pedir o repositório/notifier
app.dependency_overrides[get_user_repository] = lambda: MySQLUserRepository()
app.dependency_overrides[get_task_repository] = lambda: MySQLTaskRepository()
app.dependency_overrides[get_notification_port] = lambda: DiscordNotifierAdapter()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)