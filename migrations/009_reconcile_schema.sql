-- 009: Reconcile schema drift for databases created before later phases.
-- Safe to run on both fresh and existing databases (all statements idempotent).

-- Report items: vendor / quantity / financial capture + ETD/ETA/ready-for-sale
ALTER TABLE dds_report_items
    ADD COLUMN IF NOT EXISTS vendor VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS etd VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS eta VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS ready_for_sale VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS quantity_text VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS financial_text VARCHAR(255) NULL;

-- Tasks: numeric quantity/financial values, deadline text, overdue/blocked flags
ALTER TABLE dds_tasks
    ADD COLUMN IF NOT EXISTS quantity_value INT NULL,
    ADD COLUMN IF NOT EXISTS financial_value DECIMAL(12,2) NULL,
    ADD COLUMN IF NOT EXISTS currency VARCHAR(10) NULL,
    ADD COLUMN IF NOT EXISTS deadline_text VARCHAR(50) NULL,
    ADD COLUMN IF NOT EXISTS is_overdue BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE;

-- Insights: vendor attribution, impact, recommendation, risk tags
ALTER TABLE dds_insights
    ADD COLUMN IF NOT EXISTS vendor VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS impact TEXT NULL,
    ADD COLUMN IF NOT EXISTS recommendation TEXT NULL,
    ADD COLUMN IF NOT EXISTS risk_tags TEXT NULL;

-- Clearance materials: secondary quantity
ALTER TABLE dds_clearance_materials
    ADD COLUMN IF NOT EXISTS quantity_other INT NULL;

-- Thread summaries (per-report rollup written by the processor)
CREATE TABLE IF NOT EXISTS dds_thread_summaries (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    report_id         INT NOT NULL,
    total_anomalies   INT DEFAULT 0,
    critical_items    TEXT,
    overall_health    VARCHAR(20),
    key_risks         TEXT,
    sales_timeline    TEXT,
    priority_matrix   TEXT,
    key_highlights    TEXT,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_thread_report (report_id),
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Priority actions
CREATE TABLE IF NOT EXISTS dds_priority_actions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    report_id   INT NOT NULL,
    brand_id    INT NULL,
    person      VARCHAR(100) NOT NULL,
    action      TEXT NOT NULL,
    action_ar   TEXT,
    category    VARCHAR(100),
    urgency     VARCHAR(20),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_priority_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Password reset OTP support
CREATE TABLE IF NOT EXISTS password_reset_otps (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL,
    otp_code    VARCHAR(10) NOT NULL,
    otp_hash    VARCHAR(255) NOT NULL,
    expires_at  DATETIME NOT NULL,
    used        BOOLEAN DEFAULT FALSE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_otp_email (email),
    INDEX idx_otp_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS otp_rate_limits (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    email            VARCHAR(255) NOT NULL,
    request_count    INT DEFAULT 1,
    last_request_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_otp_rate_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
