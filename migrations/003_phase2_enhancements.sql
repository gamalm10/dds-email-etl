-- Phase 2: Important Enhancements

-- 2.1 Signature Blocks
CREATE TABLE IF NOT EXISTS dds_signatures (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    sender_email    VARCHAR(255),
    person_name     VARCHAR(255),
    title           VARCHAR(255),
    company         VARCHAR(255),
    phone           VARCHAR(100),
    email           VARCHAR(255),
    address         TEXT,
    raw_text        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    INDEX idx_signature_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.2 Inline Image Metadata
CREATE TABLE IF NOT EXISTS dds_email_images (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    content_id      VARCHAR(255),
    content_type    VARCHAR(100),
    size_bytes      INT,
    filename        VARCHAR(255),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    INDEX idx_image_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.3 Percentage/Financial Metrics
CREATE TABLE IF NOT EXISTS dds_percentage_metrics (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    brand_id        INT,
    metric_type     VARCHAR(50),
    value           DECIMAL(10,2),
    context         TEXT,
    raw_text        VARCHAR(255),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_metric_report (report_id),
    INDEX idx_metric_type (metric_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.4 Risk Language Tracking
CREATE TABLE IF NOT EXISTS dds_risk_language (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    brand_id        INT,
    phrase          VARCHAR(255),
    category        VARCHAR(50),
    severity_score  INT DEFAULT 0,
    context         TEXT,
    raw_text        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_risk_report (report_id),
    INDEX idx_risk_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.5 Report Risk Summary
ALTER TABLE dds_reports ADD COLUMN IF NOT EXISTS risk_score INT DEFAULT 0;
ALTER TABLE dds_reports ADD COLUMN IF NOT EXISTS risk_category VARCHAR(50);
