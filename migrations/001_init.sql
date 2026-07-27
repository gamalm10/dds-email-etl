CREATE TABLE IF NOT EXISTS dds_brands (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    division        VARCHAR(100) NOT NULL,
    brand_category  VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_brand (division, brand_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_reports (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    subject           VARCHAR(255) NOT NULL,
    report_date       DATE NOT NULL,
    sender            VARCHAR(255),
    recipients        TEXT,
    cc_list           TEXT,
    received_at       DATETIME NOT NULL,
    raw_html          LONGTEXT,
    raw_text          LONGTEXT,
    processing_status ENUM('pending','processing','completed','failed') DEFAULT 'pending',
    error_message     TEXT,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_report_date (report_date),
    INDEX idx_processing_status (processing_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_report_items (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    report_id           INT NOT NULL,
    brand_id            INT NOT NULL,
    availability_status ENUM('green','yellow','red','grey','black','unknown') DEFAULT 'unknown',
    milestone           TEXT,
    milestone_ar        TEXT,
    shipment_bis        TEXT,
    comments_actions    TEXT,
    comments_actions_ar TEXT,
    language            VARCHAR(10) DEFAULT 'en',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_report_id (report_id),
    INDEX idx_brand_id (brand_id),
    INDEX idx_availability (availability_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_status_history (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    brand_id        INT NOT NULL,
    report_id       INT NOT NULL,
    previous_status VARCHAR(50),
    current_status  VARCHAR(50),
    days_since_last_report INT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id) ON DELETE CASCADE,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    INDEX idx_brand_history (brand_id, report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_tasks (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    report_item_id        INT NOT NULL,
    task_description      TEXT NOT NULL,
    assigned_to           VARCHAR(255),
    deadline              DATE,
    task_category         VARCHAR(100),
    task_status           VARCHAR(50) DEFAULT 'open',
    priority              VARCHAR(20) DEFAULT 'medium',
    language              VARCHAR(10) DEFAULT 'en',
    first_seen_report_id  INT,
    last_seen_report_id   INT,
    occurrence_count      INT DEFAULT 1,
    is_resolved           BOOLEAN DEFAULT FALSE,
    resolved_at_report_id INT,
    embedding             LONGBLOB,
    FOREIGN KEY (report_item_id) REFERENCES dds_report_items(id) ON DELETE CASCADE,
    FOREIGN KEY (first_seen_report_id) REFERENCES dds_reports(id),
    FOREIGN KEY (last_seen_report_id) REFERENCES dds_reports(id),
    FOREIGN KEY (resolved_at_report_id) REFERENCES dds_reports(id),
    INDEX idx_assigned_to (assigned_to),
    INDEX idx_deadline (deadline),
    INDEX idx_task_category (task_category),
    INDEX idx_task_status (task_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_insights (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    brand_id        INT,
    insight_type    VARCHAR(50),
    description     TEXT NOT NULL,
    description_ar  TEXT,
    language        VARCHAR(10) DEFAULT 'en',
    severity        VARCHAR(20),
    anomaly_score   DECIMAL(5,4),
    matched_anomaly_id INT,
    related_task_id INT,
    embedding       LONGBLOB,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    FOREIGN KEY (matched_anomaly_id) REFERENCES dds_insights(id),
    FOREIGN KEY (related_task_id) REFERENCES dds_tasks(id),
    INDEX idx_insight_type (insight_type),
    INDEX idx_severity (severity),
    INDEX idx_anomaly_score (anomaly_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_anomaly_log (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    source_insight_id   INT NOT NULL,
    matched_insight_id  INT NOT NULL,
    similarity_score    DECIMAL(5,4) NOT NULL,
    source_report_id    INT NOT NULL,
    matched_report_id   INT NOT NULL,
    detected_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_reviewed         BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (source_insight_id) REFERENCES dds_insights(id) ON DELETE CASCADE,
    FOREIGN KEY (matched_insight_id) REFERENCES dds_insights(id),
    FOREIGN KEY (source_report_id) REFERENCES dds_reports(id),
    FOREIGN KEY (matched_report_id) REFERENCES dds_reports(id),
    INDEX idx_similarity_score (similarity_score),
    INDEX idx_detected_at (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dds_processing_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    report_id   INT NOT NULL,
    step        VARCHAR(50),
    status      VARCHAR(20),
    message     TEXT,
    duration_ms INT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    INDEX idx_report_step (report_id, step)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
