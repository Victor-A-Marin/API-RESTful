import jwt
from datetime import date
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

# Dependências do Core obtidas via Injeção de Dependência no main.py
from .service import UserService, TaskService, SECRET_KEY, ALGORITHM

app = FastAPI(
    title="Hexagonal Task Manager API",
    description="Interface Swagger (Adapter) desacoplada do core da aplicação.",
    version="1.0.0"
)

security_scheme = HTTPBearer()
blacklisted_tokens = set()

# Instâncias dos serviços serão injetadas aqui pelo main.py
_user_service: Optional[UserService] = None
_task_service: Optional[TaskService] = None

def init_api(user_svc: UserService, task_svc: TaskService):
    global _user_service, _task_service
    _user_service = user_svc
    _task_service = task_svc

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    if token in blacklisted_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido (Logged out).")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado.")

# DTOs para validação de entrada do Swagger
class UserCreateDTO(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "Usuário"

class UserUpdateDTO(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

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

class LoginDTO(BaseModel):
    email: EmailStr
    password: str

# --- ROTAS ---

@app.post("/auth/login", tags=["Autenticação"])
def login(payload: LoginDTO):
    try:
        return _user_service.login(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/logout", tags=["Autenticação"])
def logout(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    blacklisted_tokens.add(credentials.credentials)
    return {"message": "Logout realizado com sucesso."}

@app.post("/users", status_code=status.HTTP_201_CREATED, tags=["Usuários"])
def create_user(payload: UserCreateDTO):
    try:
        return _user_service.create_user(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", tags=["Usuários"])
def get_user(user_id: int, current_user = Depends(get_current_user)):
    try:
        return _user_service.get_user(user_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/users/{user_id}", tags=["Usuários"])
def update_user(user_id: int, payload: UserUpdateDTO, current_user = Depends(get_current_user)):
    try:
        return _user_service.update_user(user_id, payload.model_dump(exclude_unset=True))
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}", tags=["Usuários"])
def delete_user(user_id: int, current_user = Depends(get_current_user)):
    try:
        return _user_service.delete_user(user_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/tasks", status_code=status.HTTP_201_CREATED, tags=["Tarefas"])
def create_task(payload: TaskCreateDTO, current_user = Depends(get_current_user)):
    try:
        return _task_service.create_task(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks/{task_id}", tags=["Tarefas"])
def get_task(task_id: int, current_user = Depends(get_current_user)):
    try:
        return _task_service.get_task(task_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/tasks", tags=["Tarefas"])
def list_tasks(assignedTo: int = Query(..., description="ID do Usuário"), current_user = Depends(get_current_user)):
    return _task_service.get_tasks_by_user(assignedTo)

@app.put("/tasks/{task_id}", tags=["Tarefas"])
def update_task(task_id: int, payload: TaskUpdateDTO, current_user = Depends(get_current_user)):
    try:
        return _task_service.update_task(task_id, payload.model_dump(exclude_unset=True))
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/tasks/{task_id}", tags=["Tarefas"])
def delete_task(task_id: int, current_user = Depends(get_current_user)):
    try:
        return _task_service.delete_task(task_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))