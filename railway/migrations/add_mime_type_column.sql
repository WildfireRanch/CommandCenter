-- Add mime_type column to kb_documents table
-- This allows us to store different file types (Google Docs, PDFs, Spreadsheets)

ALTER TABLE kb_documents
ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100);

-- Set default mime type for existing records
UPDATE kb_documents
SET mime_type = 'application/vnd.google-apps.document'
WHERE mime_type IS NULL;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_kb_documents_mime_type ON kb_documents(mime_type);
