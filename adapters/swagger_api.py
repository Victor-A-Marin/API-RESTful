from datetime import date
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status, Query
from pydantic import BaseModel, EmailStr

from core.dependencies import (
    get_user_service, 
    get_task_service, 
    get_current_user, 
    RoleChecker, 
    security_scheme, 
    blacklisted_tokens
)
from core.service import UserService, TaskService

app = FastAPI(
    title="Hexagonal Task Manager API",
    description="API protegida por RBAC com injeção limpa e serviços desacoplados.",
    version="1.0.0"
)

ADMIN = "Administrador"
USER = "Usuário"
GUEST = "Convidado"

# ---------------------------------------------------------
# DTOs
# ---------------------------------------------------------
class LoginDTO(BaseModel):
    email: EmailStr
    password: str

class UserCreateDTO(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = USER

class UserUpdateDTO(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

class UserPublicResponseDTO(BaseModel):
    username: str
    email: EmailStr

class TaskCreateDTO(BaseModel):
    title: str
    description: Optional[str] = ""
    status: Optional[str] = "pendente"
    due_date: Optional[date] = None
    user_ids: Optional[List[int]] = []

class TaskUpdateDTO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    user_ids: Optional[List[int]] = None


# ---------------------------------------------------------
# ROTAS DE AUTENTICAÇÃO
# ---------------------------------------------------------
@app.post("/auth/login", tags=["Autenticação"])
def login(payload: LoginDTO, user_service: UserService = Depends(get_user_service)):
    try:
        return user_service.login(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/auth/logout", tags=["Autenticação"])
def logout(credentials = Depends(security_scheme)):
    blacklisted_tokens.add(credentials.credentials)
    return {"message": "Logout realizado com sucesso."}


# ---------------------------------------------------------
# ROTAS DE USUÁRIOS
# ---------------------------------------------------------
@app.post("/users", status_code=status.HTTP_201_CREATED, tags=["Usuários"], dependencies=[Depends(RoleChecker([ADMIN]))])
def create_user(payload: UserCreateDTO, user_service: UserService = Depends(get_user_service)):
    try:
        return user_service.create_user(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", tags=["Usuários"])
def get_user(user_id: int, current_user: dict = Depends(get_current_user), user_service: UserService = Depends(get_user_service)):
    try:
        user_data = user_service.get_user(user_id)
        if current_user.get("role") == ADMIN:
            return user_data
        return UserPublicResponseDTO(**user_data)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/users/{user_id}", tags=["Usuários"], dependencies=[Depends(RoleChecker([ADMIN]))])
def update_user(user_id: int, payload: UserUpdateDTO, user_service: UserService = Depends(get_user_service)):
    try:
        return user_service.update_user(user_id, payload.model_dump(exclude_unset=True))
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}", tags=["Usuários"], dependencies=[Depends(RoleChecker([ADMIN]))])
def delete_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    try:
        return user_service.delete_user(user_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------
# ROTAS DE TAREFAS
# ---------------------------------------------------------
@app.post("/tasks", status_code=status.HTTP_201_CREATED, tags=["Tarefas"], dependencies=[Depends(RoleChecker([ADMIN, USER]))])
def create_task(payload: TaskCreateDTO, task_service: TaskService = Depends(get_task_service)):
    try:
        return task_service.create_task(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks/{task_id}", tags=["Tarefas"], dependencies=[Depends(get_current_user)])
def get_task(task_id: int, task_service: TaskService = Depends(get_task_service)):
    try:
        return task_service.get_task(task_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/tasks", tags=["Tarefas"], dependencies=[Depends(get_current_user)])
def list_tasks(
    assignedTo: int = Query(..., description="ID do Usuário"),
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: int = Query(10, ge=1, le=100, description="Limite de registros retornados"),
    task_service: TaskService = Depends(get_task_service)
):
    """Listar tarefas de um usuário com paginação."""
    return task_service.get_tasks_by_user(assignedTo, skip=skip, limit=limit)

@app.put("/tasks/{task_id}", tags=["Tarefas"], dependencies=[Depends(RoleChecker([ADMIN, USER]))])
def update_task(task_id: int, payload: TaskUpdateDTO, task_service: TaskService = Depends(get_task_service)):
    try:
        return task_service.update_task(task_id, payload.model_dump(exclude_unset=True))
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/tasks/{task_id}", tags=["Tarefas"], dependencies=[Depends(RoleChecker([ADMIN, USER]))])
def delete_task(task_id: int, task_service: TaskService = Depends(get_task_service)):
    try:
        return task_service.delete_task(task_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))