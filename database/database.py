from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import create_engine, text, Column, Integer, String, Text, Date, DateTime, Enum
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ⚠️ Troca SUA_SENHA pela senha do seu MySQL
DATABASE_URL = "mysql+pymysql://root:vam123@localhost:3306/task_manager"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

# ------------------------------------------------------------
# Modelos ORM — representam as tabelas do banco
# São diferentes das entidades de domínio (user.py, task.py)
# ------------------------------------------------------------

class UserModel(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(100), nullable=False)
    email         = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False, default="")
    role          = Column(
                        Enum("Administrador", "Usuário", "Convidado"),
                        nullable=False,
                        default="Usuário"
                    )
    deleted_at    = Column(DateTime, nullable=True, default=None)
    created_at    = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))


class TaskModel(Base):
    __tablename__ = "tasks"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(
                      Enum("pendente", "em andamento", "concluída"),
                      nullable=False,
                      default="pendente"
                  )
    due_date    = Column(Date, nullable=True)
    created_at  = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at  = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))


class UserTaskModel(Base):
    __tablename__ = "user_tasks"

    user_id     = Column(Integer, primary_key=True)
    task_id     = Column(Integer, primary_key=True)
    assigned_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))


# ------------------------------------------------------------
# MySQL User Repository
# Implementa o mesmo contrato do InMemoryUserRepository
# ------------------------------------------------------------

class MySQLUserRepository:
    def __init__(self) -> None:
        self.Session = SessionLocal

    def save(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        with self.Session() as session:
            if user_data.get("id") is None:
                # INSERT
                model = UserModel(
                    username      = user_data["username"],
                    email         = user_data["email"],
                    password_hash = user_data.get("password_hash", ""),
                    role          = user_data.get("role", "Usuário"),
                    deleted_at    = None,
                )
                session.add(model)
                session.commit()
                session.refresh(model)
                return self._to_dict(model)
            else:
                # UPDATE
                model = session.get(UserModel, user_data["id"])
                if not model:
                    raise KeyError("Usuário não encontrado.")
                model.username      = user_data.get("username", model.username)
                model.email         = user_data.get("email", model.email)
                model.password_hash = user_data.get("password_hash", model.password_hash)
                model.role          = user_data.get("role", model.role)
                session.commit()
                session.refresh(model)
                return self._to_dict(model)

    def find_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self.Session() as session:
            model = (
                session.query(UserModel)
                .filter(
                    UserModel.id == user_id,
                    UserModel.deleted_at.is_(None)
                )
                .first()
            )

            return self._to_dict(model) if model else None

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self.Session() as session:
            model = (
                session.query(UserModel)
                .filter(
                    UserModel.email == email,
                    UserModel.deleted_at.is_(None)
                )
                .first()
            )

            return self._to_dict(model) if model else None

    def delete(self, user_id: int) -> bool:
        with self.Session() as session:
            model = session.get(UserModel, user_id)
            if not model:
                return False
            model.deleted_at = datetime.now(timezone.utc)
            session.commit()
            return True

    def _to_dict(self, model: UserModel) -> Dict[str, Any]:
        with self.Session() as session:
            task_ids = [
                row.task_id for row in
                session.query(UserTaskModel).filter_by(user_id=model.id).all()
            ]
        return {
            "id":            model.id,
            "username":      model.username,
            "email":         model.email,
            "password_hash": model.password_hash,
            "role":          model.role,
            "deleted_at":    model.deleted_at.isoformat() if model.deleted_at else None,
            "task_ids":      task_ids,
        }


# ------------------------------------------------------------
# MySQL Task Repository
# Implementa o mesmo contrato do InMemoryTaskRepository
# ------------------------------------------------------------

class MySQLTaskRepository:
    def __init__(self) -> None:
        self.Session = SessionLocal

    def save(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        with self.Session() as session:
            user_ids = task_data.get("user_ids", [])

            if task_data.get("id") is None:
                # INSERT
                model = TaskModel(
                    title       = task_data["title"],
                    description = task_data.get("description", ""),
                    status      = task_data.get("status", "pendente"),
                    due_date    = task_data.get("due_date"),
                )
                session.add(model)
                session.commit()
                session.refresh(model)
            else:
                # UPDATE
                model = session.get(TaskModel, task_data["id"])
                if not model:
                    raise KeyError("Tarefa não encontrada.")
                model.title       = task_data.get("title", model.title)
                model.description = task_data.get("description", model.description)
                model.status      = task_data.get("status", model.status)
                model.due_date    = task_data.get("due_date", model.due_date)
                session.commit()
                session.refresh(model)

            # Sincroniza a tabela user_tasks
            session.query(UserTaskModel).filter_by(task_id=model.id).delete()
            for uid in user_ids:
                session.add(UserTaskModel(user_id=uid, task_id=model.id))
            session.commit()

            return self._to_dict(model, user_ids)

    def find_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self.Session() as session:
            model = session.get(TaskModel, task_id)
            if not model:
                return None
            user_ids = [r.user_id for r in session.query(UserTaskModel).filter_by(task_id=task_id).all()]
            return self._to_dict(model, user_ids)

    def find_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        with self.Session() as session:

            tasks = (
                session.query(TaskModel)
                .join(
                    UserTaskModel,
                    TaskModel.id == UserTaskModel.task_id
                )
                .filter(UserTaskModel.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )

            result = []

            for task in tasks:
                user_ids = [
                    row.user_id
                    for row in session.query(UserTaskModel)
                    .filter_by(task_id=task.id)
                    .all()
                ]

                result.append(
                    self._to_dict(task, user_ids)
                )

            return result

    def delete(self, task_id: int) -> bool:
        with self.Session() as session:
            model = session.get(TaskModel, task_id)
            if not model:
                return False
            session.query(UserTaskModel).filter_by(task_id=task_id).delete()
            session.delete(model)
            session.commit()
            return True

    def _to_dict(self, model: TaskModel, user_ids: List[int]) -> Dict[str, Any]:
        return {
            "id":          model.id,
            "title":       model.title,
            "description": model.description,
            "status":      model.status,
            "due_date":    model.due_date.isoformat() if model.due_date else None,
            "user_ids":    user_ids,
        }