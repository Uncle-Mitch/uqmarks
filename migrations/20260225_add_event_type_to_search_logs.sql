ALTER TABLE search_logs
ADD COLUMN IF NOT EXISTS event_type VARCHAR(16);

UPDATE search_logs
SET event_type = 'add'
WHERE event_type IS NULL;

ALTER TABLE search_logs
ALTER COLUMN event_type SET DEFAULT 'add';

ALTER TABLE search_logs
ALTER COLUMN event_type SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'search_logs_event_type_check'
    ) THEN
        ALTER TABLE search_logs
        ADD CONSTRAINT search_logs_event_type_check
        CHECK (event_type IN ('page_load', 'add'));
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_search_logs_event_type ON search_logs (event_type);
