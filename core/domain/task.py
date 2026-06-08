from datetime import date, datetime, timezone
from typing import Optional, Dict, Any, List


class Task:
    """Entidade de domínio para tarefas.

    Esta classe mantém a lógica de domínio isolada da infraestrutura.
    Não há nenhuma chamada direta ao banco de dados nesta camada.
    """

    STATUS_INCOMPLETE = "pendente"
    STATUS_ON_GOING = "em andamento"
    STATUS_COMPLETE = "concluída"
    VALID_STATUSES = {STATUS_INCOMPLETE, STATUS_ON_GOING, STATUS_COMPLETE}

    def __init__(
        self,
        title: str,
        description: str = "",
        status: str = STATUS_INCOMPLETE,
        due_date: Optional[date] = None,
        task_id: Optional[int] = None,
        user_ids: Optional[List[int]] = None,
    ) -> None:
        if not title or not title.strip():
            raise ValueError("O título da task é obrigatório.")

        if status not in self.VALID_STATUSES:
            raise ValueError(f"Status inválido: {status}")

        self.id = task_id
        self.title = title.strip()
        self.description = description.strip()
        self.status = status
        self.due_date = due_date
        self.user_ids = user_ids[:] if user_ids is not None else []

    @classmethod
    def create(
        cls,
        title: str,
        description: str = "",
        status: str = STATUS_INCOMPLETE,
        due_date: Optional[date] = None,
        user_ids: Optional[List[int]] = None,
    ) -> "Task":
        """Cria uma nova tarefa de domínio sem depender da infraestrutura."""
        return cls(
            title=title,
            description=description,
            status=status,
            due_date=due_date,
            user_ids=user_ids,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Inicializa uma task a partir de um dicionário de dados."""
        due_date = data.get("due_date")
        if isinstance(due_date, str):
            due_date = date.fromisoformat(due_date)

        user_ids = data.get("user_ids") or []
        if not isinstance(user_ids, list):
            raise ValueError("user_ids deve ser uma lista de inteiros.")

        user_ids = [int(user_id) for user_id in user_ids if user_id is not None]

        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", cls.STATUS_INCOMPLETE),
            due_date=due_date,
            task_id=data.get("id"),
            user_ids=user_ids,
        )

    def update(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        due_date: Optional[date] = None,
        user_ids: Optional[List[int]] = None,
    ) -> None:
        """Atualiza os atributos da task em memória."""
        if title is not None:
            if not title.strip():
                raise ValueError("O título da task é obrigatório.")
            self.title = title.strip()

        if description is not None:
            self.description = description.strip()

        if status is not None:
            if status not in self.VALID_STATUSES:
                raise ValueError(f"Status inválido: {status}")
            self.status = status

        if due_date is not None:
            self.due_date = due_date

        if user_ids is not None:
            self.user_ids = user_ids[:]

    def mark_complete(self) -> None:
        """Marca a task como concluída."""
        self.status = self.STATUS_COMPLETE

    def mark_on_going(self) -> None:
        """Marca a task como em andamento."""
        self.status = self.STATUS_ON_GOING

    def mark_incomplete(self) -> None:
        """Marca a task como incompleta."""
        self.status = self.STATUS_INCOMPLETE

    def add_user_id(self, user_id: int) -> None:
        """Associa um usuário à task por ID."""
        if user_id not in self.user_ids:
            self.user_ids.append(user_id)

    def remove_user_id(self, user_id: int) -> None:
        """Remove a associação de usuário à task por ID."""
        self.user_ids = [existing for existing in self.user_ids if existing != user_id]

    def is_overdue(self, today: Optional[date] = None) -> bool:
        """Retorna True se a task está vencida e ainda incompleta."""
        if self.due_date is None:
            return False

        today = today or datetime.now(timezone.utc).date()
        return self.status != self.STATUS_COMPLETE and self.due_date < today

    def to_dict(self) -> Dict[str, Any]:
        """Retorna os dados da task em formato de dicionário."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "user_ids": self.user_ids,
        }

    def __repr__(self) -> str:
        return (
            f"Task(id={self.id!r}, title={self.title!r}, description={self.description!r}, "
            f"status={self.status!r}, due_date={self.due_date!r}, user_ids={self.user_ids!r})"
        )
