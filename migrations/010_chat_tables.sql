-- 010: Chat + RAG embeddings tables.
-- Safe to run on both fresh and existing databases (idempotent).

CREATE TABLE IF NOT EXISTS dds_chat_conversations (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    report_id   INT NULL COMMENT 'NULL = global chat, set = per-report chat',
    title       VARCHAR(255) NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE SET NULL,
    INDEX idx_chat_conv_user (user_id),
    INDEX idx_chat_conv_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dds_chat_messages (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    role            ENUM('user', 'assistant', 'system') NOT NULL,
    content         TEXT NOT NULL,
    citations       JSON NULL COMMENT '[{"type":"report_item","id":123,"label":"PHC Clutch"}]',
    tokens_used     INT NULL,
    model           VARCHAR(100) NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES dds_chat_conversations(id) ON DELETE CASCADE,
    INDEX idx_chat_msg_conv (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS dds_report_embeddings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    source_type     ENUM('report_item', 'task', 'insight', 'email_chunk', 'thread_summary') NOT NULL,
    source_id       INT NOT NULL COMMENT 'ID of the source record',
    report_id       INT NOT NULL,
    brand_id        INT NULL,
    chunk_text      TEXT NOT NULL COMMENT 'The text that was embedded',
    v               VECTOR(1536) NOT NULL COMMENT 'OpenAI text-embedding-3-small vector',
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id) ON DELETE SET NULL,
    INDEX idx_emb_source (source_type, source_id),
    INDEX idx_emb_report (report_id),
    UNIQUE KEY uk_emb_source (source_type, source_id),
    VECTOR INDEX (v) M=16 DISTANCE=cosine
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
