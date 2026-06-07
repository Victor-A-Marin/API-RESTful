

CREATE DATABASE IF NOT EXISTS task_manager
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE task_manager;

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


CREATE INDEX idx_tasks_status    ON tasks      (status);
CREATE INDEX idx_tasks_due_date  ON tasks      (due_date);
CREATE INDEX idx_ut_task_id      ON user_tasks (task_id);
CREATE INDEX idx_users_deleted   ON users      (deleted_at);

USE task_manager;
SELECT * FROM users;
