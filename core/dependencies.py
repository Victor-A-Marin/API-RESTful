import jwt
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .ports import UserRepositoryPort, TaskRepositoryPort, NotificationPort
from .service import UserService, TaskService, SECRET_KEY, ALGORITHM

# ---------------------------------------------------------
# 1. Configurações de Segurança
# ---------------------------------------------------------
security_scheme = HTTPBearer()
blacklisted_tokens = set()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    token = credentials.credentials
    if token in blacklisted_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido (Logged out).")
    try:
        # Tenta decodificar
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado.")
    except jwt.PyJWTError as e:
        # AQUI ESTÁ O SEGREDO: Vamos imprimir o erro no terminal
        print(f"ERRO REAL DO JWT: {str(e)}") 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Erro interno: {str(e)}")

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if not user_role or user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Acesso negado. Privilégios insuficientes para esta ação."
            )
        return current_user

# ---------------------------------------------------------
# 2. Injeção de Dependências (Serviços e Repositórios)
# ---------------------------------------------------------
def get_user_repository() -> UserRepositoryPort:
    raise NotImplementedError("Injetado no boot da aplicação.")

def get_task_repository() -> TaskRepositoryPort:
    raise NotImplementedError("Injetado no boot da aplicação.")

def get_notification_port() -> NotificationPort:
    raise NotImplementedError("Injetado no boot da aplicação (ex: DiscordAdapter).")

def get_user_service(
    repo: UserRepositoryPort = Depends(get_user_repository),
    notifier: NotificationPort = Depends(get_notification_port)
) -> UserService:
    return UserService(repo, notifier)

def get_task_service(
    task_repo: TaskRepositoryPort = Depends(get_task_repository),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    notifier: NotificationPort = Depends(get_notification_port)
) -> TaskService:
    return TaskService(task_repo, user_repo, notifier)