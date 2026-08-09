-- Phase 6: Brand attribution for report-level extractions

ALTER TABLE dds_priority_actions
    ADD COLUMN brand_id INT NULL,
    ADD CONSTRAINT fk_priority_action_brand FOREIGN KEY (brand_id) REFERENCES dds_brands(id),
    ADD INDEX idx_priority_action_brand (brand_id);

ALTER TABLE dds_payment_terms
    ADD INDEX idx_payment_brand (brand_id);

ALTER TABLE dds_negotiations
    ADD INDEX idx_nego_brand (brand_id);

ALTER TABLE dds_lead_times
    ADD INDEX idx_lead_brand (brand_id);

ALTER TABLE dds_risk_language
    ADD INDEX idx_risk_brand (brand_id);
