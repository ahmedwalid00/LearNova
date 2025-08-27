-- Initialize PGVector extension
-- This script runs automatically when the container starts for the first time

-- Create the vector extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE NOTICE 'PGVector extension successfully installed';
    ELSE
        RAISE EXCEPTION 'PGVector extension failed to install';
    END IF;
END $$;
