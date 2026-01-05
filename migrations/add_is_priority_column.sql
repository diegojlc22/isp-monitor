-- Add is_priority column to equipments table
-- This allows marking equipment for priority monitoring (capacity planning, security audit, etc)

ALTER TABLE equipments 
ADD COLUMN IF NOT EXISTS is_priority BOOLEAN DEFAULT FALSE;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_equipments_is_priority ON equipments(is_priority) WHERE is_priority = TRUE;

COMMENT ON COLUMN equipments.is_priority IS 'Marks equipment for priority monitoring in advanced features';
