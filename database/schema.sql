-- ============================================================
--  Sistema de Gestão de Tarefas Colaborativas
--  Schema MySQL — alinhado com as entidades User e Task
-- ============================================================

CREATE DATABASE IF NOT EXISTS task_manager
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE task_manager;

-- ------------------------------------------------------------
--  USERS
--  Representa a entidade User (core/domain/user.py)
--  - role segue os valores de VALID_ROLES da entidade
--  - deleted_at implementa o soft delete do InMemoryUserRepository
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INT           NOT NULL AUTO_INCREMENT,
    username      VARCHAR(100)  NOT NULL,
    email         VARCHAR(255)  NOT NULL,
    password_hash VARCHAR(255)  NOT NULL DEFAULT '',
    role          ENUM(
                    'Administrador',
                    'Usuário',
                    'Convidado'
                  )             NOT NULL DEFAULT 'Usuário',
    deleted_at    DATETIME      NULL DEFAULT NULL,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
);

-- ------------------------------------------------------------
--  TASKS
--  Representa a entidade Task (core/domain/task.py)
--  - status segue os valores de VALID_STATUSES da entidade
--  - due_date é opcional (nullable), igual ao domínio
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    id          INT           NOT NULL AUTO_INCREMENT,
    title       VARCHAR(255)  NOT NULL,
    description TEXT          NULL DEFAULT NULL,
    status      ENUM(
                  'pendente',
                  'em andamento',
                  'concluída'
                )             NOT NULL DEFAULT 'pendente',
    due_date    DATE          NULL DEFAULT NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id)
);

-- ------------------------------------------------------------
--  USER_TASKS  (tabela de junção N:N)
--  Representa o relacionamento user_ids / task_ids
--  que existe nas duas entidades de domínio
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_tasks (
    user_id     INT      NOT NULL,
    task_id     INT      NOT NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, task_id),

    CONSTRAINT fk_ut_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE,
sys_config
    CONSTRAINT fk_ut_task
        FOREIGN KEY (task_id) REFERENCES tasks (id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
--  Índices para queries frequentes
--  (baseados nos métodos dos ports: find_by_user_id, find_by_email)
-- ------------------------------------------------------------
CREATE INDEX idx_tasks_status    ON tasks      (status);
CREATE INDEX idx_tasks_due_date  ON tasks      (due_date);
CREATE INDEX idx_ut_task_id      ON user_tasks (task_id);
CREATE INDEX idx_users_deleted   ON users      (deleted_at);

USE task_manager;
SELECT * FROM users;
