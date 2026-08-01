-- Phase 1: Critical Gaps

-- 1.1 Clearance/Material Detail Table
CREATE TABLE IF NOT EXISTS dds_clearance_materials (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    material_code   VARCHAR(100),
    description     TEXT,
    description_ar  TEXT,
    quantity        INT,
    brand_id        INT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_material_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.2 General Ordering Rules
CREATE TABLE IF NOT EXISTS dds_ordering_rules (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    report_id         INT NOT NULL,
    max_amount_usd    DECIMAL(12,2),
    max_amount_eur    DECIMAL(12,2),
    margin_percent    DECIMAL(5,2),
    sales_months      INT,
    requires_approval BOOLEAN DEFAULT TRUE,
    rule_text         TEXT,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.3 Email Thread Structure
CREATE TABLE IF NOT EXISTS dds_email_threads (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    message_id      VARCHAR(255),
    thread_index    INT,
    subject         VARCHAR(255),
    sender          VARCHAR(255),
    sent_at         DATETIME,
    depth           INT DEFAULT 0,
    parent_id       INT,
    is_dds_email    BOOLEAN DEFAULT FALSE,
    brand_count     INT DEFAULT 0,
    has_table       BOOLEAN DEFAULT FALSE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    INDEX idx_thread_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
