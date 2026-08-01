-- DDS Frontend - Authentication & Authorization Tables

CREATE TABLE IF NOT EXISTS roles (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(50) UNIQUE NOT NULL,
    description     TEXT,
    permissions     JSON,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(100) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role_id         INT NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    INDEX idx_email (email),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sessions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    refresh_token   VARCHAR(500) NOT NULL,
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_token (refresh_token(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    action          VARCHAR(100) NOT NULL,
    resource        VARCHAR(100),
    resource_id     INT,
    details         JSON,
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
('admin', 'Full system access', '["*"]'),
('manager', 'Manage reports and users', '["reports:*", "users:read"]'),
('viewer', 'Read-only access', '["reports:read"]')
ON DUPLICATE KEY UPDATE name=name;
