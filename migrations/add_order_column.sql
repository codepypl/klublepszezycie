-- Migration: Add order column to pages table
-- Date: 2025-08-29
-- Description: Adds order column for sorting pages

-- Add order column with default value 0
ALTER TABLE pages ADD COLUMN IF NOT EXISTS "order" INTEGER DEFAULT 0;

-- Update existing records to have order = 0
UPDATE pages SET "order" = 0 WHERE "order" IS NULL;

-- Make order column NOT NULL
ALTER TABLE pages ALTER COLUMN "order" SET NOT NULL;

-- Add index for better performance on sorting
CREATE INDEX IF NOT EXISTS idx_pages_order ON pages("order");
