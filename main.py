import uvicorn
from database import InMemoryUserRepository, InMemoryTaskRepository
from core.service import UserService, TaskService
from core.swagger_api import app, init_api

# 1. Instancia os adaptadores de infraestrutura de banco de dados
user_repo = InMemoryUserRepository()
task_repo = InMemoryTaskRepository()

# 2. Instancia os serviços do Core injetando os repositórios
user_service = UserService(user_repo)
task_service = TaskService(task_repo, user_repo)

# 3. Inicializa o adaptador da API injetando os serviços configurados
init_api(user_service, task_service)

# Expõe a aplicação para o servidor HTTP externo
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)