-- Migration: System Instruction Document Mappings
-- Date: 2025-11-21
-- Description: Create mapping table for linking documents to system instruction template slots

-- Create the mappings table
CREATE TABLE IF NOT EXISTS system_instruction_document_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id) ON DELETE CASCADE NOT NULL,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE NOT NULL,
  template_slot TEXT NOT NULL,
  display_order INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Ensure a document can only be mapped once per slot per client
  UNIQUE(client_id, document_id, template_slot)
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_doc_mappings_client ON system_instruction_document_mappings(client_id);
CREATE INDEX IF NOT EXISTS idx_doc_mappings_document ON system_instruction_document_mappings(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_mappings_slot ON system_instruction_document_mappings(template_slot);

-- Add comments
COMMENT ON TABLE system_instruction_document_mappings IS 'Maps documents to template slots in system instructions';
COMMENT ON COLUMN system_instruction_document_mappings.template_slot IS 'Template placeholder name (e.g., pm_models_ref, domain_specific_models_ref)';
COMMENT ON COLUMN system_instruction_document_mappings.display_order IS 'Order for multiple documents in same slot';

-- Valid template slots (as CHECK constraint)
ALTER TABLE system_instruction_document_mappings
ADD CONSTRAINT valid_template_slots CHECK (
  template_slot IN (
    'pm_models_ref',              -- Project management models/frameworks
    'domain_specific_models_ref', -- Industry/domain-specific frameworks
    'language_guideline_ref',     -- Writing/communication style guides
    'knowledge_base_ref_2',       -- Additional knowledge base reference
    'knowledge_base_ref_4',       -- Team capability profiles
    'client_gold_standard_example' -- Gold standard example documents
  )
);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_doc_mapping_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_doc_mapping_updated_at_trigger
BEFORE UPDATE ON system_instruction_document_mappings
FOR EACH ROW
EXECUTE FUNCTION update_doc_mapping_updated_at();

-- When a document is mapped, automatically mark it as core
CREATE OR REPLACE FUNCTION mark_mapped_document_as_core()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE documents
  SET is_core_document = true
  WHERE id = NEW.document_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mark_document_core_on_mapping
AFTER INSERT ON system_instruction_document_mappings
FOR EACH ROW
EXECUTE FUNCTION mark_mapped_document_as_core();
