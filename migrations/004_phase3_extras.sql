-- Phase 3: Additional Features

-- 3.1 Payment Terms
CREATE TABLE IF NOT EXISTS dds_payment_terms (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    report_id         INT NOT NULL,
    brand_id          INT,
    payment_method    VARCHAR(100),
    deposit_pct       DECIMAL(5,2),
    balance_pct       DECIMAL(5,2),
    expected_date     DATE,
    raw_text          TEXT,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_payment_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3.2 Discount/Negotiation Tracking
CREATE TABLE IF NOT EXISTS dds_negotiations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    brand_id        INT,
    type            VARCHAR(50),
    percentage      DECIMAL(5,2),
    status          VARCHAR(50) DEFAULT 'proposed',
    context         TEXT,
    raw_text        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_nego_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3.3 Lead Time Tracking
CREATE TABLE IF NOT EXISTS dds_lead_times (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    report_id       INT NOT NULL,
    brand_id        INT,
    days            INT,
    reference_date  DATE,
    status          VARCHAR(50),
    context         TEXT,
    raw_text        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    INDEX idx_lead_report (report_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
