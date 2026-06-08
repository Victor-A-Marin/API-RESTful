import jwt
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext

from .domain.user import User
from .domain.task import Task
from .ports import UserRepositoryPort, TaskRepositoryPort, NotificationPort

SECRET_KEY = "super-secret-key-para-fins-de-demonstracao"
ALGORITHM = "HS256"

# Configuração do Passlib para hashing com bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, repo: UserRepositoryPort, notifier: NotificationPort) -> None:
        self.repo = repo
        self.notifier = notifier

    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.repo.find_by_email(data.get("email", "")):
            raise ValueError("Email já cadastrado.")
        
        # Gerando hash real da senha
        raw_password = data.get("password", "")
        data["password_hash"] = pwd_context.hash(raw_password)
        
        user = User.from_dict(data)
        saved = self.repo.save(user.to_dict())
        
        self.notifier.notify_user_created(saved["username"], saved["email"])
        return saved

    def get_user(self, user_id: int) -> Dict[str, Any]:
        data = self.repo.find_by_id(user_id)
        if not data or data.get("deleted_at"):
            raise KeyError("Usuário não encontrado.")
        return data

    def update_user(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        current_data = self.get_user(user_id)
        user = User.from_dict(current_data)
        
        user.update(
            username=data.get("username"),
            email=data.get("email"),
            role=data.get("role")
        )
        return self.repo.save(user.to_dict())

    def delete_user(self, user_id: int) -> Dict[str, Any]:
        user = self.get_user(user_id)
        self.repo.delete(user_id)
        self.notifier.notify_user_deleted(user["username"])
        return {"message": "Usuário removido com sucesso (Soft Delete)."}

    def login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        user_data = self.repo.find_by_email(data.get("email", ""))
        if not user_data or user_data.get("deleted_at"):
            raise ValueError("Credenciais inválidas.")
        
        # Verificando a senha contra o hash
        if not pwd_context.verify(data.get("password", ""), user_data.get("password_hash", "")):
            raise ValueError("Credenciais inválidas.")

        payload = {
            "sub": str(user_data["id"]),  # <-- AQUI: Cast para string!
            "email": user_data["email"],
            "role": user_data.get("role", "Usuário"),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=2)).timestamp())
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}


class TaskService:
    def __init__(self, task_repo: TaskRepositoryPort, user_repo: UserRepositoryPort, notifier: NotificationPort) -> None:
        self.task_repo = task_repo
        self.user_repo = user_repo
        self.notifier = notifier

    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for u_id in data.get("user_ids", []):
            if not self.user_repo.find_by_id(u_id):
                raise ValueError(f"Usuário associado com id {u_id} não existe.")
        
        task = Task.from_dict(data)
        saved_task_dict = self.task_repo.save(task.to_dict())
        
        for u_id in saved_task_dict["user_ids"]:
            u_data = self.user_repo.find_by_id(u_id)
            if u_data:
                u_obj = User.from_dict(u_data)
                u_obj.add_task_id(saved_task_dict["id"])
                self.user_repo.save(u_obj.to_dict())

        self.notifier.notify_task_created(saved_task_dict["title"], saved_task_dict["status"])
        return saved_task_dict

    def get_task(self, task_id: int) -> Dict[str, Any]:
        data = self.task_repo.find_by_id(task_id)
        if not data:
            raise KeyError("Tarefa não encontrada.")
        return data

    def get_tasks_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        # Adicionado controle de paginação
        return self.task_repo.find_by_user_id(user_id, skip=skip, limit=limit)

    def update_task(self, task_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        current_data = self.get_task(task_id)
        task = Task.from_dict(current_data)
        
        due_date_val = data.get("due_date")
        if isinstance(due_date_val, str):
            due_date_val = date.fromisoformat(due_date_val)

        task.update(
            title=data.get("title"),
            description=data.get("description"),
            status=data.get("status"),
            due_date=due_date_val,
            user_ids=data.get("user_ids")
        )
        updated = self.task_repo.save(task.to_dict())
        self.notifier.notify_task_updated(updated["title"], updated["status"])
        return updated

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        current_data = self.get_task(task_id)
        for u_id in current_data.get("user_ids", []):
            u_data = self.user_repo.find_by_id(u_id)
            if u_data:
                u_obj = User.from_dict(u_data)
                u_obj.remove_task_id(task_id)
                self.user_repo.save(u_obj.to_dict())
                
        self.task_repo.delete(task_id)
        self.notifier.notify_task_deleted(current_data["title"])
        return {"message": "Tarefa deletada com sucesso."}