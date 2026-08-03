CREATE TABLE IF NOT EXISTS dds_fetched_emails (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(50),
    subject TEXT,
    sender VARCHAR(255),
    received_at DATETIME,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'pending',
    report_id INT,
    error_message TEXT,
    FOREIGN KEY (report_id) REFERENCES dds_reports(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
