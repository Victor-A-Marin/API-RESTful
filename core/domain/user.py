from __future__ import annotations

from typing import Optional, Dict, Any, List


class User:
    """Entidade de domínio do usuário.

    Esta classe não faz nenhuma interação direta com o banco de dados.
    A persistência deve ser tratada por um adaptador/porta no padrão hexagonal.
    """

    ROLE_ADMIN = "Administrador"
    ROLE_USER = "Usuário"
    ROLE_GUEST = "Convidado"
    VALID_ROLES = {ROLE_ADMIN, ROLE_USER, ROLE_GUEST}

    def __init__(
        self,
        username: str,
        email: str,
        password_hash: str = "",
        role: str = ROLE_USER,
        user_id: Optional[int] = None,
        task_ids: Optional[List[int]] = None,
    ) -> None:
        if role not in self.VALID_ROLES:
            raise ValueError(f"Role inválido: {role}")

        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.task_ids = task_ids[:] if task_ids is not None else []

    @classmethod
    def create(
        cls,
        username: str,
        email: str,
        password_hash: str = "",
        role: str = ROLE_USER,
        task_ids: Optional[List[int]] = None,
    ) -> "User":
        """Cria um novo usuário sem dependência de infraestrutura."""
        return cls(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            task_ids=task_ids,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Inicializa um usuário a partir de dados simples."""
        task_ids = data.get("task_ids") or []
        if not isinstance(task_ids, list):
            raise ValueError("task_ids deve ser uma lista de inteiros.")

        task_ids = [int(task_id) for task_id in task_ids if task_id is not None]

        return cls(
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", cls.ROLE_USER),
            user_id=data.get("id"),
            task_ids=task_ids,
        )

    def update(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password_hash: Optional[str] = None,
        role: Optional[str] = None,
        task_ids: Optional[List[int]] = None,
    ) -> None:
        """Atualiza os atributos do usuário em memória."""
        if username is not None:
            self.username = username
        if email is not None:
            self.email = email
        if password_hash is not None:
            self.password_hash = password_hash
        if role is not None:
            if role not in self.VALID_ROLES:
                raise ValueError(f"Role inválido: {role}")
            self.role = role
        if task_ids is not None:
            self.task_ids = task_ids[:]

    def add_task_id(self, task_id: int) -> None:
        """Associa o ID de uma task ao usuário."""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)

    def remove_task_id(self, task_id: int) -> None:
        """Remove o ID de uma task associada ao usuário."""
        self.task_ids = [existing for existing in self.task_ids if existing != task_id]

    def to_dict(self) -> Dict[str, Any]:
        """Retorna os dados do usuário em formato de dicionário."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "task_ids": self.task_ids,
        }

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, username={self.username!r}, "
            f"email={self.email!r}, password_hash={self.password_hash!r}, "
            f"role={self.role!r}, task_ids={self.task_ids!r})"
        )

    def is_admin(self) -> bool:
        """Retorna True se o usuário for administrador."""
        return self.role == self.ROLE_ADMIN

    def is_user(self) -> bool:
        """Retorna True se o usuário for usuário padrão."""
        return self.role == self.ROLE_USER

    def is_guest(self) -> bool:
        """Retorna True se o usuário for convidado."""
        return self.role == self.ROLE_GUEST
