import pymysql
from sqlalchemy import create_engine, text
from database.database import Base, engine, MySQLUserRepository
from core.service import UserService
from adapters.discord import DiscordNotifierAdapter

# --- CONFIGURAÇÃO ---
SENHA_MYSQL = 'SUA_SENHA_AQUI' # <--- COLOQUE SUA SENHA AQUI
DB_NAME = "task_manager"
# --------------------

def preparar_ambiente():
    print("1. Tentando criar o banco de dados...")
    # Conecta no servidor sem selecionar banco para poder criar o DB
    conn = pymysql.connect(host='localhost', user='root', password='vam123')
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.close()
    conn.close()
    print(f"Banco '{DB_NAME}' pronto.")

    print("2. Criando tabelas no banco...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas.")

    print("3. Criando usuário admin...")
    repo = MySQLUserRepository()
    notifier = DiscordNotifierAdapter("https://webhook.site/teste")
    service = UserService(repo, notifier)

    try:
        service.create_user({
            "username": "admin",
            "email": "admin@teste.com",
            "password": "123",
            "role": "Administrador"
        })
        print("SUCESSO: Usuário admin criado!")
    except Exception as e:
        print(f"Aviso: Não foi possível criar o admin (pode já existir): {e}")

if __name__ == "__main__":
    try:
        preparar_ambiente()
    except Exception as e:
        print(f"\nERRO CRÍTICO: {e}")
        print("\nVerifique se o MySQL está rodando e se a senha está correta no script.")