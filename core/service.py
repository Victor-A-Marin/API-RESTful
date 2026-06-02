import jwt
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List

from .domain.user import User
from .domain.task import Task
from .ports import UserRepositoryPort, TaskRepositoryPort

SECRET_KEY = "super-secret-key-para-fins-de-demonstracao"
ALGORITHM = "HS256"

class UserService:
    def __init__(self, repo: UserRepositoryPort) -> None:
        self.repo = repo

    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.repo.find_by_email(data.get("email", "")):
            raise ValueError("Email já cadastrado.")
        data["password_hash"] = f"hashed_{data.get('password', '123')}"
        user = User.from_dict(data)
        return self.repo.save(user.to_dict())

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
        self.get_user(user_id)
        self.repo.delete(user_id)
        return {"message": "Usuário removido com sucesso (Soft Delete)."}

    def login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        user_data = self.repo.find_by_email(data.get("email", ""))
        if not user_data or user_data.get("deleted_at"):
            raise ValueError("Credenciais inválidas.")
        
        expected_hash = f"hashed_{data.get('password', '')}"
        if user_data.get("password_hash") != expected_hash:
            raise ValueError("Credenciais inválidas.")

        payload = {
            "sub": user_data["id"],
            "email": user_data["email"],
            "exp": datetime.utcnow() + timedelta(hours=2)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}


class TaskService:
    def __init__(self, task_repo: TaskRepositoryPort, user_repo: UserRepositoryPort) -> None:
        self.task_repo = task_repo
        self.user_repo = user_repo

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
                
        return saved_task_dict

    def get_task(self, task_id: int) -> Dict[str, Any]:
        data = self.task_repo.find_by_id(task_id)
        if not data:
            raise KeyError("Tarefa não encontrada.")
        return data

    def get_tasks_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        return self.task_repo.find_by_user_id(user_id)

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
        return self.task_repo.save(task.to_dict())

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        current_data = self.get_task(task_id)
        for u_id in current_data.get("user_ids", []):
            u_data = self.user_repo.find_by_id(u_id)
            if u_data:
                u_obj = User.from_dict(u_data)
                u_obj.remove_task_id(task_id)
                self.user_repo.save(u_obj.to_dict())
                
        self.task_repo.delete(task_id)
        return {"message": "Tarefa deletada com sucesso."}