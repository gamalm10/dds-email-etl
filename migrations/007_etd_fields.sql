-- Phase 7: ETD / ETA / Ready for Sale extraction

ALTER TABLE dds_report_items
    ADD COLUMN etd VARCHAR(100) NULL,
    ADD COLUMN eta VARCHAR(100) NULL,
    ADD COLUMN ready_for_sale VARCHAR(255) NULL;
