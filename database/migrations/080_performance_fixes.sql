-- =============================================================
-- Migration 080: Performance Fixes
-- Fixes auth_rls_initplan, multiple_permissive_policies,
-- duplicate_index, unindexed_foreign_keys, and unused_index advisories
-- =============================================================

BEGIN;

-- =============================================================
-- SECTION 1: Fix auth_rls_initplan
-- Wrap bare auth.uid()/auth.role() in (SELECT ...) subselects
-- =============================================================

-- Table: agent_handoffs, Policy: Users can view handoffs in their conversations
DROP POLICY IF EXISTS "Users can view handoffs in their conversations" ON public.agent_handoffs;
CREATE POLICY "Users can view handoffs in their conversations" ON public.agent_handoffs
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((conversation_id IN ( SELECT conversations.id
   FROM conversations
  WHERE (conversations.user_id = (SELECT auth.uid())))));

-- Table: agent_instruction_versions, Policy: Admins can manage agent instructions
DROP POLICY IF EXISTS "Admins can manage agent instructions" ON public.agent_instruction_versions;
CREATE POLICY "Admins can manage agent instructions" ON public.agent_instruction_versions
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((EXISTS ( SELECT 1
   FROM users
  WHERE ((users.id = (SELECT auth.uid())) AND ((users.role)::text = 'admin'::text)))));

-- Table: agent_knowledge_base, Policy: Admins can manage agent knowledge base
DROP POLICY IF EXISTS "Admins can manage agent knowledge base" ON public.agent_knowledge_base;
CREATE POLICY "Admins can manage agent knowledge base" ON public.agent_knowledge_base
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((EXISTS ( SELECT 1
   FROM users
  WHERE ((users.id = (SELECT auth.uid())) AND ((users.role)::text = 'admin'::text)))));

-- Table: agent_topic_mapping, Policy: Service role full access to agent_topic_mapping
DROP POLICY IF EXISTS "Service role full access to agent_topic_mapping" ON public.agent_topic_mapping;
CREATE POLICY "Service role full access to agent_topic_mapping" ON public.agent_topic_mapping
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: ai_projects, Policy: Service role has full access to ai_projects
DROP POLICY IF EXISTS "Service role has full access to ai_projects" ON public.ai_projects;
CREATE POLICY "Service role has full access to ai_projects" ON public.ai_projects
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: ai_projects, Policy: Users can manage projects in their client
DROP POLICY IF EXISTS "Users can manage projects in their client" ON public.ai_projects;
CREATE POLICY "Users can manage projects in their client" ON public.ai_projects
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: ai_projects, Policy: Users can view projects in their client
DROP POLICY IF EXISTS "Users can view projects in their client" ON public.ai_projects;
CREATE POLICY "Users can view projects in their client" ON public.ai_projects
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: api_usage_logs, Policy: Users can view api_usage_logs in their client
DROP POLICY IF EXISTS "Users can view api_usage_logs in their client" ON public.api_usage_logs;
CREATE POLICY "Users can view api_usage_logs in their client" ON public.api_usage_logs
  AS PERMISSIVE
  FOR SELECT
  TO authenticated
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: clients, Policy: Users can view their own client
DROP POLICY IF EXISTS "Users can view their own client" ON public.clients;
CREATE POLICY "Users can view their own client" ON public.clients
  AS PERMISSIVE
  FOR SELECT
  TO authenticated
  USING ((id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: compass_status_reports, Policy: Service role has full access
DROP POLICY IF EXISTS "Service role has full access" ON public.compass_status_reports;
CREATE POLICY "Service role has full access" ON public.compass_status_reports
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: compass_status_reports, Policy: Users can create their own reports
DROP POLICY IF EXISTS "Users can create their own reports" ON public.compass_status_reports;
CREATE POLICY "Users can create their own reports" ON public.compass_status_reports
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK (((SELECT auth.uid()) = user_id));

-- Table: compass_status_reports, Policy: Users can delete their own reports
DROP POLICY IF EXISTS "Users can delete their own reports" ON public.compass_status_reports;
CREATE POLICY "Users can delete their own reports" ON public.compass_status_reports
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: compass_status_reports, Policy: Users can update their own reports
DROP POLICY IF EXISTS "Users can update their own reports" ON public.compass_status_reports;
CREATE POLICY "Users can update their own reports" ON public.compass_status_reports
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: compass_status_reports, Policy: Users can view their own reports
DROP POLICY IF EXISTS "Users can view their own reports" ON public.compass_status_reports;
CREATE POLICY "Users can view their own reports" ON public.compass_status_reports
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: conversations, Policy: Users can create conversations
DROP POLICY IF EXISTS "Users can create conversations" ON public.conversations;
CREATE POLICY "Users can create conversations" ON public.conversations
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK (((SELECT auth.uid()) = user_id));

-- Table: conversations, Policy: Users can delete own conversations
DROP POLICY IF EXISTS "Users can delete own conversations" ON public.conversations;
CREATE POLICY "Users can delete own conversations" ON public.conversations
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: conversations, Policy: Users can update own conversations
DROP POLICY IF EXISTS "Users can update own conversations" ON public.conversations;
CREATE POLICY "Users can update own conversations" ON public.conversations
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: conversations, Policy: Users can view own conversations
DROP POLICY IF EXISTS "Users can view own conversations" ON public.conversations;
CREATE POLICY "Users can view own conversations" ON public.conversations
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: disco_bundle_feedback, Policy: disco_bundle_feedback_insert_policy
DROP POLICY IF EXISTS "disco_bundle_feedback_insert_policy" ON public.disco_bundle_feedback;
CREATE POLICY "disco_bundle_feedback_insert_policy" ON public.disco_bundle_feedback
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((user_id = (SELECT auth.uid())));

-- Table: disco_bundle_feedback, Policy: disco_bundle_feedback_select_policy
DROP POLICY IF EXISTS "disco_bundle_feedback_select_policy" ON public.disco_bundle_feedback;
CREATE POLICY "disco_bundle_feedback_select_policy" ON public.disco_bundle_feedback
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((bundle_id IN ( SELECT b.id
   FROM (disco_bundles b
     JOIN disco_initiative_members m ON ((b.initiative_id = m.initiative_id)))
  WHERE (m.user_id = (SELECT auth.uid())))) OR (bundle_id IN ( SELECT b.id
   FROM (disco_bundles b
     JOIN disco_initiatives i ON ((b.initiative_id = i.id)))
  WHERE (i.created_by = (SELECT auth.uid()))))));

-- Table: disco_bundles, Policy: disco_bundles_delete_policy
DROP POLICY IF EXISTS "disco_bundles_delete_policy" ON public.disco_bundles;
CREATE POLICY "disco_bundles_delete_policy" ON public.disco_bundles
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING (((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE ((disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = 'owner'::text)))) OR (initiative_id IN ( SELECT disco_initiatives.id
   FROM disco_initiatives
  WHERE (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_bundles, Policy: disco_bundles_insert_policy
DROP POLICY IF EXISTS "disco_bundles_insert_policy" ON public.disco_bundles;
CREATE POLICY "disco_bundles_insert_policy" ON public.disco_bundles
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK (((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE ((disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))) OR (initiative_id IN ( SELECT disco_initiatives.id
   FROM disco_initiatives
  WHERE (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_bundles, Policy: disco_bundles_select_policy
DROP POLICY IF EXISTS "disco_bundles_select_policy" ON public.disco_bundles;
CREATE POLICY "disco_bundles_select_policy" ON public.disco_bundles
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE (disco_initiative_members.user_id = (SELECT auth.uid())))) OR (initiative_id IN ( SELECT disco_initiatives.id
   FROM disco_initiatives
  WHERE (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_bundles, Policy: disco_bundles_update_policy
DROP POLICY IF EXISTS "disco_bundles_update_policy" ON public.disco_bundles;
CREATE POLICY "disco_bundles_update_policy" ON public.disco_bundles
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE ((disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))) OR (initiative_id IN ( SELECT disco_initiatives.id
   FROM disco_initiatives
  WHERE (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_checkpoints, Policy: Users can delete checkpoints for their initiatives
DROP POLICY IF EXISTS "Users can delete checkpoints for their initiatives" ON public.disco_checkpoints;
CREATE POLICY "Users can delete checkpoints for their initiatives" ON public.disco_checkpoints
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_checkpoints.initiative_id) AND (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_checkpoints, Policy: Users can insert checkpoints for their initiatives
DROP POLICY IF EXISTS "Users can insert checkpoints for their initiatives" ON public.disco_checkpoints;
CREATE POLICY "Users can insert checkpoints for their initiatives" ON public.disco_checkpoints
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_checkpoints.initiative_id) AND (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_checkpoints, Policy: Users can update checkpoints for their initiatives
DROP POLICY IF EXISTS "Users can update checkpoints for their initiatives" ON public.disco_checkpoints;
CREATE POLICY "Users can update checkpoints for their initiatives" ON public.disco_checkpoints
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_checkpoints.initiative_id) AND (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_checkpoints, Policy: Users can view checkpoints for their initiatives
DROP POLICY IF EXISTS "Users can view checkpoints for their initiatives" ON public.disco_checkpoints;
CREATE POLICY "Users can view checkpoints for their initiatives" ON public.disco_checkpoints
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_checkpoints.initiative_id) AND (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_conversations, Policy: disco_conversations_insert
DROP POLICY IF EXISTS "disco_conversations_insert" ON public.disco_conversations;
CREATE POLICY "disco_conversations_insert" ON public.disco_conversations
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((user_id = (SELECT auth.uid())));

-- Table: disco_conversations, Policy: disco_conversations_select
DROP POLICY IF EXISTS "disco_conversations_select" ON public.disco_conversations;
CREATE POLICY "disco_conversations_select" ON public.disco_conversations
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: disco_document_chunks, Policy: disco_chunks_select
DROP POLICY IF EXISTS "disco_chunks_select" ON public.disco_document_chunks;
CREATE POLICY "disco_chunks_select" ON public.disco_document_chunks
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (disco_documents dd
     JOIN disco_initiatives di ON ((dd.initiative_id = di.id)))
  WHERE ((dd.id = disco_document_chunks.document_id) AND ((di.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = di.id) AND (disco_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: disco_documents, Policy: disco_documents_insert
DROP POLICY IF EXISTS "disco_documents_insert" ON public.disco_documents;
CREATE POLICY "disco_documents_insert" ON public.disco_documents
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_documents.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: disco_documents, Policy: disco_documents_select
DROP POLICY IF EXISTS "disco_documents_select" ON public.disco_documents;
CREATE POLICY "disco_documents_select" ON public.disco_documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_documents.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: disco_initiative_documents, Policy: disco_init_docs_delete
DROP POLICY IF EXISTS "disco_init_docs_delete" ON public.disco_initiative_documents;
CREATE POLICY "disco_init_docs_delete" ON public.disco_initiative_documents
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives di
  WHERE ((di.id = disco_initiative_documents.initiative_id) AND ((di.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members dim
          WHERE ((dim.initiative_id = di.id) AND (dim.user_id = (SELECT auth.uid())) AND (dim.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: disco_initiative_documents, Policy: disco_init_docs_insert
DROP POLICY IF EXISTS "disco_init_docs_insert" ON public.disco_initiative_documents;
CREATE POLICY "disco_init_docs_insert" ON public.disco_initiative_documents
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK (((linked_by = (SELECT auth.uid())) AND (EXISTS ( SELECT 1
   FROM disco_initiatives di
  WHERE ((di.id = disco_initiative_documents.initiative_id) AND ((di.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members dim
          WHERE ((dim.initiative_id = di.id) AND (dim.user_id = (SELECT auth.uid())) AND (dim.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))) AND (EXISTS ( SELECT 1
   FROM documents d
  WHERE ((d.id = disco_initiative_documents.document_id) AND (d.uploaded_by = (SELECT auth.uid())))))));

-- Table: disco_initiative_documents, Policy: disco_init_docs_select
DROP POLICY IF EXISTS "disco_init_docs_select" ON public.disco_initiative_documents;
CREATE POLICY "disco_init_docs_select" ON public.disco_initiative_documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives di
  WHERE ((di.id = disco_initiative_documents.initiative_id) AND ((di.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members dim
          WHERE ((dim.initiative_id = di.id) AND (dim.user_id = (SELECT auth.uid()))))))))));

-- Table: disco_initiative_folders, Policy: Editors can manage initiative folders
DROP POLICY IF EXISTS "Editors can manage initiative folders" ON public.disco_initiative_folders;
CREATE POLICY "Editors can manage initiative folders" ON public.disco_initiative_folders
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE ((disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))));

-- Table: disco_initiative_folders, Policy: Users can view initiative folders they have access to
DROP POLICY IF EXISTS "Users can view initiative folders they have access to" ON public.disco_initiative_folders;
CREATE POLICY "Users can view initiative folders they have access to" ON public.disco_initiative_folders
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE (disco_initiative_members.user_id = (SELECT auth.uid())))));

-- Table: disco_initiative_members, Policy: disco_members_select
DROP POLICY IF EXISTS "disco_members_select" ON public.disco_initiative_members;
CREATE POLICY "disco_members_select" ON public.disco_initiative_members
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_initiative_members.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members m
          WHERE ((m.initiative_id = disco_initiatives.id) AND (m.user_id = (SELECT auth.uid()))))))))));

-- Table: disco_initiatives, Policy: disco_initiatives_delete
DROP POLICY IF EXISTS "disco_initiatives_delete" ON public.disco_initiatives;
CREATE POLICY "disco_initiatives_delete" ON public.disco_initiatives
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((created_by = (SELECT auth.uid())));

-- Table: disco_initiatives, Policy: disco_initiatives_insert
DROP POLICY IF EXISTS "disco_initiatives_insert" ON public.disco_initiatives;
CREATE POLICY "disco_initiatives_insert" ON public.disco_initiatives
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((created_by = (SELECT auth.uid())));

-- Table: disco_initiatives, Policy: disco_initiatives_select
DROP POLICY IF EXISTS "disco_initiatives_select" ON public.disco_initiatives;
CREATE POLICY "disco_initiatives_select" ON public.disco_initiatives
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
   FROM disco_initiative_members
  WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())))))));

-- Table: disco_initiatives, Policy: disco_initiatives_update
DROP POLICY IF EXISTS "disco_initiatives_update" ON public.disco_initiatives;
CREATE POLICY "disco_initiatives_update" ON public.disco_initiatives
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
   FROM disco_initiative_members
  WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text])))))));

-- Table: disco_messages, Policy: disco_messages_insert
DROP POLICY IF EXISTS "disco_messages_insert" ON public.disco_messages;
CREATE POLICY "disco_messages_insert" ON public.disco_messages
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM disco_conversations
  WHERE ((disco_conversations.id = disco_messages.conversation_id) AND (disco_conversations.user_id = (SELECT auth.uid()))))));

-- Table: disco_messages, Policy: disco_messages_select
DROP POLICY IF EXISTS "disco_messages_select" ON public.disco_messages;
CREATE POLICY "disco_messages_select" ON public.disco_messages
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_conversations
  WHERE ((disco_conversations.id = disco_messages.conversation_id) AND (disco_conversations.user_id = (SELECT auth.uid()))))));

-- Table: disco_outputs, Policy: disco_outputs_delete
DROP POLICY IF EXISTS "disco_outputs_delete" ON public.disco_outputs;
CREATE POLICY "disco_outputs_delete" ON public.disco_outputs
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_outputs.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: disco_outputs, Policy: disco_outputs_insert
DROP POLICY IF EXISTS "disco_outputs_insert" ON public.disco_outputs;
CREATE POLICY "disco_outputs_insert" ON public.disco_outputs
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_outputs.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: disco_outputs, Policy: disco_outputs_select
DROP POLICY IF EXISTS "disco_outputs_select" ON public.disco_outputs;
CREATE POLICY "disco_outputs_select" ON public.disco_outputs
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_outputs.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: disco_outputs, Policy: disco_outputs_update
DROP POLICY IF EXISTS "disco_outputs_update" ON public.disco_outputs;
CREATE POLICY "disco_outputs_update" ON public.disco_outputs
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_outputs.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: disco_prds, Policy: disco_prds_insert_policy
DROP POLICY IF EXISTS "disco_prds_insert_policy" ON public.disco_prds;
CREATE POLICY "disco_prds_insert_policy" ON public.disco_prds
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK (((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE ((disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))) OR (initiative_id IN ( SELECT disco_initiatives.id
   FROM disco_initiatives
  WHERE (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_prds, Policy: disco_prds_select_policy
DROP POLICY IF EXISTS "disco_prds_select_policy" ON public.disco_prds;
CREATE POLICY "disco_prds_select_policy" ON public.disco_prds
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE (disco_initiative_members.user_id = (SELECT auth.uid())))) OR (initiative_id IN ( SELECT disco_initiatives.id
   FROM disco_initiatives
  WHERE (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_prds, Policy: disco_prds_update_policy
DROP POLICY IF EXISTS "disco_prds_update_policy" ON public.disco_prds;
CREATE POLICY "disco_prds_update_policy" ON public.disco_prds
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((initiative_id IN ( SELECT disco_initiative_members.initiative_id
   FROM disco_initiative_members
  WHERE ((disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))) OR (initiative_id IN ( SELECT disco_initiatives.id
   FROM disco_initiatives
  WHERE (disco_initiatives.created_by = (SELECT auth.uid()))))));

-- Table: disco_run_documents, Policy: disco_run_documents_insert
DROP POLICY IF EXISTS "disco_run_documents_insert" ON public.disco_run_documents;
CREATE POLICY "disco_run_documents_insert" ON public.disco_run_documents
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM (disco_runs r
     JOIN disco_initiatives i ON ((i.id = r.initiative_id)))
  WHERE ((r.id = disco_run_documents.run_id) AND ((i.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = i.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: disco_run_documents, Policy: disco_run_documents_select
DROP POLICY IF EXISTS "disco_run_documents_select" ON public.disco_run_documents;
CREATE POLICY "disco_run_documents_select" ON public.disco_run_documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (disco_runs r
     JOIN disco_initiatives i ON ((i.id = r.initiative_id)))
  WHERE ((r.id = disco_run_documents.run_id) AND ((i.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = i.id) AND (disco_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: disco_runs, Policy: disco_runs_insert
DROP POLICY IF EXISTS "disco_runs_insert" ON public.disco_runs;
CREATE POLICY "disco_runs_insert" ON public.disco_runs
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_runs.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: disco_runs, Policy: disco_runs_select
DROP POLICY IF EXISTS "disco_runs_select" ON public.disco_runs;
CREATE POLICY "disco_runs_select" ON public.disco_runs
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_runs.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: disco_runs, Policy: disco_runs_update
DROP POLICY IF EXISTS "disco_runs_update" ON public.disco_runs;
CREATE POLICY "disco_runs_update" ON public.disco_runs
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM disco_initiatives
  WHERE ((disco_initiatives.id = disco_runs.initiative_id) AND ((disco_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM disco_initiative_members
          WHERE ((disco_initiative_members.initiative_id = disco_initiatives.id) AND (disco_initiative_members.user_id = (SELECT auth.uid())) AND (disco_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: document_chunks, Policy: Users can view chunks of own documents
DROP POLICY IF EXISTS "Users can view chunks of own documents" ON public.document_chunks;
CREATE POLICY "Users can view chunks of own documents" ON public.document_chunks
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM documents
  WHERE ((documents.id = document_chunks.document_id) AND (documents.uploaded_by = (SELECT auth.uid()))))));

-- Table: document_classifications, Policy: Users can update document classifications
DROP POLICY IF EXISTS "Users can update document classifications" ON public.document_classifications;
CREATE POLICY "Users can update document classifications" ON public.document_classifications
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (documents d
     JOIN users u ON ((d.client_id = u.client_id)))
  WHERE ((d.id = document_classifications.document_id) AND (u.id = (SELECT auth.uid()))))));

-- Table: document_classifications, Policy: Users can view document classifications
DROP POLICY IF EXISTS "Users can view document classifications" ON public.document_classifications;
CREATE POLICY "Users can view document classifications" ON public.document_classifications
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (documents d
     JOIN users u ON ((d.client_id = u.client_id)))
  WHERE ((d.id = document_classifications.document_id) AND (u.id = (SELECT auth.uid()))))));

-- Table: document_tags, Policy: document_tags_delete
DROP POLICY IF EXISTS "document_tags_delete" ON public.document_tags;
CREATE POLICY "document_tags_delete" ON public.document_tags
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((document_id IN ( SELECT documents.id
   FROM documents
  WHERE (documents.user_id = (SELECT auth.uid())))));

-- Table: document_tags, Policy: document_tags_insert
DROP POLICY IF EXISTS "document_tags_insert" ON public.document_tags;
CREATE POLICY "document_tags_insert" ON public.document_tags
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((document_id IN ( SELECT documents.id
   FROM documents
  WHERE (documents.user_id = (SELECT auth.uid())))));

-- Table: document_tags, Policy: document_tags_select
DROP POLICY IF EXISTS "document_tags_select" ON public.document_tags;
CREATE POLICY "document_tags_select" ON public.document_tags
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((document_id IN ( SELECT documents.id
   FROM documents
  WHERE (documents.user_id = (SELECT auth.uid())))));

-- Table: document_tags, Policy: document_tags_update
DROP POLICY IF EXISTS "document_tags_update" ON public.document_tags;
CREATE POLICY "document_tags_update" ON public.document_tags
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((document_id IN ( SELECT documents.id
   FROM documents
  WHERE (documents.user_id = (SELECT auth.uid())))));

-- Table: documents, Policy: Users can delete own documents
DROP POLICY IF EXISTS "Users can delete own documents" ON public.documents;
CREATE POLICY "Users can delete own documents" ON public.documents
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((uploaded_by = (SELECT auth.uid())));

-- Table: documents, Policy: Users can update own documents
DROP POLICY IF EXISTS "Users can update own documents" ON public.documents;
CREATE POLICY "Users can update own documents" ON public.documents
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((uploaded_by = (SELECT auth.uid())));

-- Table: documents, Policy: Users can upload documents
DROP POLICY IF EXISTS "Users can upload documents" ON public.documents;
CREATE POLICY "Users can upload documents" ON public.documents
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((uploaded_by = (SELECT auth.uid())));

-- Table: documents, Policy: Users can view own documents
DROP POLICY IF EXISTS "Users can view own documents" ON public.documents;
CREATE POLICY "Users can view own documents" ON public.documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((uploaded_by = (SELECT auth.uid())));

-- Table: engagement_level_history, Policy: Service role has full access to engagement_level_history
DROP POLICY IF EXISTS "Service role has full access to engagement_level_history" ON public.engagement_level_history;
CREATE POLICY "Service role has full access to engagement_level_history" ON public.engagement_level_history
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: engagement_level_history, Policy: Users can view engagement history in their client
DROP POLICY IF EXISTS "Users can view engagement history in their client" ON public.engagement_level_history;
CREATE POLICY "Users can view engagement history in their client" ON public.engagement_level_history
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: google_drive_sync_log, Policy: Users can insert own sync logs
DROP POLICY IF EXISTS "Users can insert own sync logs" ON public.google_drive_sync_log;
CREATE POLICY "Users can insert own sync logs" ON public.google_drive_sync_log
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK (((SELECT auth.uid()) = user_id));

-- Table: google_drive_sync_log, Policy: Users can update own sync logs
DROP POLICY IF EXISTS "Users can update own sync logs" ON public.google_drive_sync_log;
CREATE POLICY "Users can update own sync logs" ON public.google_drive_sync_log
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: google_drive_sync_log, Policy: Users can view own sync logs
DROP POLICY IF EXISTS "Users can view own sync logs" ON public.google_drive_sync_log;
CREATE POLICY "Users can view own sync logs" ON public.google_drive_sync_log
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: google_drive_tokens, Policy: Users can manage own Google Drive tokens
DROP POLICY IF EXISTS "Users can manage own Google Drive tokens" ON public.google_drive_tokens;
CREATE POLICY "Users can manage own Google Drive tokens" ON public.google_drive_tokens
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: graph_sync_log, Policy: Service role full access to sync logs
DROP POLICY IF EXISTS "Service role full access to sync logs" ON public.graph_sync_log;
CREATE POLICY "Service role full access to sync logs" ON public.graph_sync_log
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: graph_sync_log, Policy: Users can view own client sync logs
DROP POLICY IF EXISTS "Users can view own client sync logs" ON public.graph_sync_log;
CREATE POLICY "Users can view own client sync logs" ON public.graph_sync_log
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: graph_sync_state, Policy: Service role full access to sync state
DROP POLICY IF EXISTS "Service role full access to sync state" ON public.graph_sync_state;
CREATE POLICY "Service role full access to sync state" ON public.graph_sync_state
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: graph_sync_state, Policy: Users can view own client sync state
DROP POLICY IF EXISTS "Users can view own client sync state" ON public.graph_sync_state;
CREATE POLICY "Users can view own client sync state" ON public.graph_sync_state
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: help_chunks, Policy: Admins see all help chunks
DROP POLICY IF EXISTS "Admins see all help chunks" ON public.help_chunks;
CREATE POLICY "Admins see all help chunks" ON public.help_chunks
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((( SELECT users.role
   FROM users
  WHERE (users.id = (SELECT auth.uid()))))::text = 'admin'::text));

-- Table: help_chunks, Policy: Users see role-appropriate help chunks
DROP POLICY IF EXISTS "Users see role-appropriate help chunks" ON public.help_chunks;
CREATE POLICY "Users see role-appropriate help chunks" ON public.help_chunks
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((( SELECT users.role
   FROM users
  WHERE (users.id = (SELECT auth.uid()))))::text = ANY (role_access)));

-- Table: help_conversations, Policy: Users see own help conversations
DROP POLICY IF EXISTS "Users see own help conversations" ON public.help_conversations;
CREATE POLICY "Users see own help conversations" ON public.help_conversations
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: help_documents, Policy: Admins see all help content
DROP POLICY IF EXISTS "Admins see all help content" ON public.help_documents;
CREATE POLICY "Admins see all help content" ON public.help_documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((( SELECT users.role
   FROM users
  WHERE (users.id = (SELECT auth.uid()))))::text = 'admin'::text));

-- Table: help_documents, Policy: Users see role-appropriate help content
DROP POLICY IF EXISTS "Users see role-appropriate help content" ON public.help_documents;
CREATE POLICY "Users see role-appropriate help content" ON public.help_documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((( SELECT users.role
   FROM users
  WHERE (users.id = (SELECT auth.uid()))))::text = ANY (role_access)));

-- Table: help_messages, Policy: Users see own help messages
DROP POLICY IF EXISTS "Users see own help messages" ON public.help_messages;
CREATE POLICY "Users see own help messages" ON public.help_messages
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((conversation_id IN ( SELECT help_conversations.id
   FROM help_conversations
  WHERE (help_conversations.user_id = (SELECT auth.uid())))));

-- Table: knowledge_gaps, Policy: Service role full access to knowledge_gaps
DROP POLICY IF EXISTS "Service role full access to knowledge_gaps" ON public.knowledge_gaps;
CREATE POLICY "Service role full access to knowledge_gaps" ON public.knowledge_gaps
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: knowledge_gaps, Policy: Users can view knowledge gaps for their clients
DROP POLICY IF EXISTS "Users can view knowledge gaps for their clients" ON public.knowledge_gaps;
CREATE POLICY "Users can view knowledge gaps for their clients" ON public.knowledge_gaps
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))) OR (client_id IS NULL)));

-- Table: meeting_room_messages, Policy: Service role has full access to meeting_room_messages
DROP POLICY IF EXISTS "Service role has full access to meeting_room_messages" ON public.meeting_room_messages;
CREATE POLICY "Service role has full access to meeting_room_messages" ON public.meeting_room_messages
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: meeting_room_messages, Policy: Users can create messages in their meetings
DROP POLICY IF EXISTS "Users can create messages in their meetings" ON public.meeting_room_messages;
CREATE POLICY "Users can create messages in their meetings" ON public.meeting_room_messages
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((meeting_room_id IN ( SELECT meeting_rooms.id
   FROM meeting_rooms
  WHERE (meeting_rooms.user_id = (SELECT auth.uid())))));

-- Table: meeting_room_messages, Policy: Users can view messages in their meetings
DROP POLICY IF EXISTS "Users can view messages in their meetings" ON public.meeting_room_messages;
CREATE POLICY "Users can view messages in their meetings" ON public.meeting_room_messages
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((meeting_room_id IN ( SELECT meeting_rooms.id
   FROM meeting_rooms
  WHERE (meeting_rooms.user_id = (SELECT auth.uid())))));

-- Table: meeting_room_participants, Policy: Service role has full access to meeting_room_participants
DROP POLICY IF EXISTS "Service role has full access to meeting_room_participants" ON public.meeting_room_participants;
CREATE POLICY "Service role has full access to meeting_room_participants" ON public.meeting_room_participants
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: meeting_room_participants, Policy: Users can manage participants in their meetings
DROP POLICY IF EXISTS "Users can manage participants in their meetings" ON public.meeting_room_participants;
CREATE POLICY "Users can manage participants in their meetings" ON public.meeting_room_participants
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((meeting_room_id IN ( SELECT meeting_rooms.id
   FROM meeting_rooms
  WHERE (meeting_rooms.user_id = (SELECT auth.uid())))));

-- Table: meeting_room_participants, Policy: Users can view participants in their meetings
DROP POLICY IF EXISTS "Users can view participants in their meetings" ON public.meeting_room_participants;
CREATE POLICY "Users can view participants in their meetings" ON public.meeting_room_participants
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((meeting_room_id IN ( SELECT meeting_rooms.id
   FROM meeting_rooms
  WHERE (meeting_rooms.user_id = (SELECT auth.uid())))));

-- Table: meeting_rooms, Policy: Service role has full access to meeting_rooms
DROP POLICY IF EXISTS "Service role has full access to meeting_rooms" ON public.meeting_rooms;
CREATE POLICY "Service role has full access to meeting_rooms" ON public.meeting_rooms
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: meeting_rooms, Policy: Users can create meeting rooms
DROP POLICY IF EXISTS "Users can create meeting rooms" ON public.meeting_rooms;
CREATE POLICY "Users can create meeting rooms" ON public.meeting_rooms
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((user_id = (SELECT auth.uid())));

-- Table: meeting_rooms, Policy: Users can delete their own meeting rooms
DROP POLICY IF EXISTS "Users can delete their own meeting rooms" ON public.meeting_rooms;
CREATE POLICY "Users can delete their own meeting rooms" ON public.meeting_rooms
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: meeting_rooms, Policy: Users can update their own meeting rooms
DROP POLICY IF EXISTS "Users can update their own meeting rooms" ON public.meeting_rooms;
CREATE POLICY "Users can update their own meeting rooms" ON public.meeting_rooms
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: meeting_rooms, Policy: Users can view their own meeting rooms
DROP POLICY IF EXISTS "Users can view their own meeting rooms" ON public.meeting_rooms;
CREATE POLICY "Users can view their own meeting rooms" ON public.meeting_rooms
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: meeting_transcripts, Policy: Users can manage their transcripts
DROP POLICY IF EXISTS "Users can manage their transcripts" ON public.meeting_transcripts;
CREATE POLICY "Users can manage their transcripts" ON public.meeting_transcripts
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: meeting_transcripts, Policy: Users can view their transcripts
DROP POLICY IF EXISTS "Users can view their transcripts" ON public.meeting_transcripts;
CREATE POLICY "Users can view their transcripts" ON public.meeting_transcripts
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: message_documents, Policy: message_documents_delete_policy
DROP POLICY IF EXISTS "message_documents_delete_policy" ON public.message_documents;
CREATE POLICY "message_documents_delete_policy" ON public.message_documents
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (messages m
     JOIN conversations c ON ((m.conversation_id = c.id)))
  WHERE ((m.id = message_documents.message_id) AND (c.user_id = (SELECT auth.uid()))))));

-- Table: message_documents, Policy: message_documents_insert_policy
DROP POLICY IF EXISTS "message_documents_insert_policy" ON public.message_documents;
CREATE POLICY "message_documents_insert_policy" ON public.message_documents
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM (messages m
     JOIN conversations c ON ((m.conversation_id = c.id)))
  WHERE ((m.id = message_documents.message_id) AND (c.user_id = (SELECT auth.uid()))))));

-- Table: message_documents, Policy: message_documents_select_policy
DROP POLICY IF EXISTS "message_documents_select_policy" ON public.message_documents;
CREATE POLICY "message_documents_select_policy" ON public.message_documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (messages m
     JOIN conversations c ON ((m.conversation_id = c.id)))
  WHERE ((m.id = message_documents.message_id) AND (c.user_id = (SELECT auth.uid()))))));

-- Table: messages, Policy: Users can create messages in own conversations
DROP POLICY IF EXISTS "Users can create messages in own conversations" ON public.messages;
CREATE POLICY "Users can create messages in own conversations" ON public.messages
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM conversations
  WHERE ((conversations.id = messages.conversation_id) AND (conversations.user_id = (SELECT auth.uid()))))));

-- Table: messages, Policy: Users can view messages in own conversations
DROP POLICY IF EXISTS "Users can view messages in own conversations" ON public.messages;
CREATE POLICY "Users can view messages in own conversations" ON public.messages
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM conversations
  WHERE ((conversations.id = messages.conversation_id) AND (conversations.user_id = (SELECT auth.uid()))))));

-- Table: oauth_states, Policy: Users can manage own OAuth states
DROP POLICY IF EXISTS "Users can manage own OAuth states" ON public.oauth_states;
CREATE POLICY "Users can manage own OAuth states" ON public.oauth_states
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: obsidian_sync_log, Policy: Service role has full access to obsidian_sync_log
DROP POLICY IF EXISTS "Service role has full access to obsidian_sync_log" ON public.obsidian_sync_log;
CREATE POLICY "Service role has full access to obsidian_sync_log" ON public.obsidian_sync_log
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: obsidian_sync_log, Policy: Users can manage their own sync logs
DROP POLICY IF EXISTS "Users can manage their own sync logs" ON public.obsidian_sync_log;
CREATE POLICY "Users can manage their own sync logs" ON public.obsidian_sync_log
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: obsidian_sync_log, Policy: Users can view their own sync logs
DROP POLICY IF EXISTS "Users can view their own sync logs" ON public.obsidian_sync_log;
CREATE POLICY "Users can view their own sync logs" ON public.obsidian_sync_log
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: obsidian_sync_state, Policy: Service role has full access to obsidian_sync_state
DROP POLICY IF EXISTS "Service role has full access to obsidian_sync_state" ON public.obsidian_sync_state;
CREATE POLICY "Service role has full access to obsidian_sync_state" ON public.obsidian_sync_state
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: obsidian_sync_state, Policy: Users can manage sync state for their configs
DROP POLICY IF EXISTS "Users can manage sync state for their configs" ON public.obsidian_sync_state;
CREATE POLICY "Users can manage sync state for their configs" ON public.obsidian_sync_state
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((config_id IN ( SELECT obsidian_vault_configs.id
   FROM obsidian_vault_configs
  WHERE (obsidian_vault_configs.user_id = (SELECT auth.uid())))));

-- Table: obsidian_sync_state, Policy: Users can view sync state for their configs
DROP POLICY IF EXISTS "Users can view sync state for their configs" ON public.obsidian_sync_state;
CREATE POLICY "Users can view sync state for their configs" ON public.obsidian_sync_state
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((config_id IN ( SELECT obsidian_vault_configs.id
   FROM obsidian_vault_configs
  WHERE (obsidian_vault_configs.user_id = (SELECT auth.uid())))));

-- Table: obsidian_vault_configs, Policy: Service role has full access to obsidian_vault_configs
DROP POLICY IF EXISTS "Service role has full access to obsidian_vault_configs" ON public.obsidian_vault_configs;
CREATE POLICY "Service role has full access to obsidian_vault_configs" ON public.obsidian_vault_configs
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: obsidian_vault_configs, Policy: Users can manage their own vault configs
DROP POLICY IF EXISTS "Users can manage their own vault configs" ON public.obsidian_vault_configs;
CREATE POLICY "Users can manage their own vault configs" ON public.obsidian_vault_configs
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: obsidian_vault_configs, Policy: Users can view their own vault configs
DROP POLICY IF EXISTS "Users can view their own vault configs" ON public.obsidian_vault_configs;
CREATE POLICY "Users can view their own vault configs" ON public.obsidian_vault_configs
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: project_candidates, Policy: Users can update project candidates in their client
DROP POLICY IF EXISTS "Users can update project candidates in their client" ON public.project_candidates;
CREATE POLICY "Users can update project candidates in their client" ON public.project_candidates
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: project_candidates, Policy: Users can view project candidates in their client
DROP POLICY IF EXISTS "Users can view project candidates in their client" ON public.project_candidates;
CREATE POLICY "Users can view project candidates in their client" ON public.project_candidates
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: project_conversations, Policy: Service role has full access to project_conversations
DROP POLICY IF EXISTS "Service role has full access to project_conversations" ON public.project_conversations;
CREATE POLICY "Service role has full access to project_conversations" ON public.project_conversations
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: project_conversations, Policy: Users can create project conversations in their client
DROP POLICY IF EXISTS "Users can create project conversations in their client" ON public.project_conversations;
CREATE POLICY "Users can create project conversations in their client" ON public.project_conversations
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: project_conversations, Policy: Users can view project conversations in their client
DROP POLICY IF EXISTS "Users can view project conversations in their client" ON public.project_conversations;
CREATE POLICY "Users can view project conversations in their client" ON public.project_conversations
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: project_documents, Policy: project_docs_delete
DROP POLICY IF EXISTS "project_docs_delete" ON public.project_documents;
CREATE POLICY "project_docs_delete" ON public.project_documents
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (ai_projects p
     JOIN users u ON ((u.client_id = p.client_id)))
  WHERE ((p.id = project_documents.project_id) AND (u.id = (SELECT auth.uid()))))));

-- Table: project_documents, Policy: project_docs_insert
DROP POLICY IF EXISTS "project_docs_insert" ON public.project_documents;
CREATE POLICY "project_docs_insert" ON public.project_documents
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK (((linked_by = (SELECT auth.uid())) AND (EXISTS ( SELECT 1
   FROM (ai_projects p
     JOIN users u ON ((u.client_id = p.client_id)))
  WHERE ((p.id = project_documents.project_id) AND (u.id = (SELECT auth.uid())))))));

-- Table: project_documents, Policy: project_docs_select
DROP POLICY IF EXISTS "project_docs_select" ON public.project_documents;
CREATE POLICY "project_docs_select" ON public.project_documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (ai_projects p
     JOIN users u ON ((u.client_id = p.client_id)))
  WHERE ((p.id = project_documents.project_id) AND (u.id = (SELECT auth.uid()))))));

-- Table: project_stakeholder_link, Policy: Service role has full access to project_stakeholder_link
DROP POLICY IF EXISTS "Service role has full access to project_stakeholder_link" ON public.project_stakeholder_link;
CREATE POLICY "Service role has full access to project_stakeholder_link" ON public.project_stakeholder_link
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: project_stakeholder_link, Policy: Users can manage project stakeholder links
DROP POLICY IF EXISTS "Users can manage project stakeholder links" ON public.project_stakeholder_link;
CREATE POLICY "Users can manage project stakeholder links" ON public.project_stakeholder_link
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((project_id IN ( SELECT ai_projects.id
   FROM ai_projects
  WHERE (ai_projects.client_id IN ( SELECT users.client_id
           FROM users
          WHERE (users.id = (SELECT auth.uid())))))));

-- Table: project_stakeholder_link, Policy: Users can view project stakeholder links
DROP POLICY IF EXISTS "Users can view project stakeholder links" ON public.project_stakeholder_link;
CREATE POLICY "Users can view project stakeholder links" ON public.project_stakeholder_link
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((project_id IN ( SELECT ai_projects.id
   FROM ai_projects
  WHERE (ai_projects.client_id IN ( SELECT users.client_id
           FROM users
          WHERE (users.id = (SELECT auth.uid())))))));

-- Table: project_tasks, Policy: Service role has full access to project_tasks
DROP POLICY IF EXISTS "Service role has full access to project_tasks" ON public.project_tasks;
CREATE POLICY "Service role has full access to project_tasks" ON public.project_tasks
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: project_tasks, Policy: Users can manage tasks in their client
DROP POLICY IF EXISTS "Users can manage tasks in their client" ON public.project_tasks;
CREATE POLICY "Users can manage tasks in their client" ON public.project_tasks
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: project_tasks, Policy: Users can view tasks in their client
DROP POLICY IF EXISTS "Users can view tasks in their client" ON public.project_tasks;
CREATE POLICY "Users can view tasks in their client" ON public.project_tasks
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: projects, Policy: Users can create own projects
DROP POLICY IF EXISTS "Users can create own projects" ON public.projects;
CREATE POLICY "Users can create own projects" ON public.projects
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK (((SELECT auth.uid()) = user_id));

-- Table: projects, Policy: Users can delete own projects
DROP POLICY IF EXISTS "Users can delete own projects" ON public.projects;
CREATE POLICY "Users can delete own projects" ON public.projects
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: projects, Policy: Users can update own projects
DROP POLICY IF EXISTS "Users can update own projects" ON public.projects;
CREATE POLICY "Users can update own projects" ON public.projects
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: projects, Policy: Users can view own projects
DROP POLICY IF EXISTS "Users can view own projects" ON public.projects;
CREATE POLICY "Users can view own projects" ON public.projects
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((SELECT auth.uid()) = user_id));

-- Table: purdy_conversations, Policy: purdy_conversations_insert
DROP POLICY IF EXISTS "purdy_conversations_insert" ON public.purdy_conversations;
CREATE POLICY "purdy_conversations_insert" ON public.purdy_conversations
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((user_id = (SELECT auth.uid())));

-- Table: purdy_conversations, Policy: purdy_conversations_select
DROP POLICY IF EXISTS "purdy_conversations_select" ON public.purdy_conversations;
CREATE POLICY "purdy_conversations_select" ON public.purdy_conversations
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: purdy_document_chunks, Policy: purdy_chunks_select
DROP POLICY IF EXISTS "purdy_chunks_select" ON public.purdy_document_chunks;
CREATE POLICY "purdy_chunks_select" ON public.purdy_document_chunks
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM (purdy_documents pd
     JOIN purdy_initiatives pi ON ((pd.initiative_id = pi.id)))
  WHERE ((pd.id = purdy_document_chunks.document_id) AND ((pi.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM purdy_initiative_members
          WHERE ((purdy_initiative_members.initiative_id = pi.id) AND (purdy_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: purdy_documents, Policy: purdy_documents_insert
DROP POLICY IF EXISTS "purdy_documents_insert" ON public.purdy_documents;
CREATE POLICY "purdy_documents_insert" ON public.purdy_documents
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM purdy_initiatives
  WHERE ((purdy_initiatives.id = purdy_documents.initiative_id) AND ((purdy_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM purdy_initiative_members
          WHERE ((purdy_initiative_members.initiative_id = purdy_initiatives.id) AND (purdy_initiative_members.user_id = (SELECT auth.uid())) AND (purdy_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text]))))))))));

-- Table: purdy_documents, Policy: purdy_documents_select
DROP POLICY IF EXISTS "purdy_documents_select" ON public.purdy_documents;
CREATE POLICY "purdy_documents_select" ON public.purdy_documents
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM purdy_initiatives
  WHERE ((purdy_initiatives.id = purdy_documents.initiative_id) AND ((purdy_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM purdy_initiative_members
          WHERE ((purdy_initiative_members.initiative_id = purdy_initiatives.id) AND (purdy_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: purdy_initiative_members, Policy: purdy_members_select
DROP POLICY IF EXISTS "purdy_members_select" ON public.purdy_initiative_members;
CREATE POLICY "purdy_members_select" ON public.purdy_initiative_members
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM purdy_initiatives
  WHERE ((purdy_initiatives.id = purdy_initiative_members.initiative_id) AND ((purdy_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM purdy_initiative_members m
          WHERE ((m.initiative_id = purdy_initiatives.id) AND (m.user_id = (SELECT auth.uid()))))))))));

-- Table: purdy_initiatives, Policy: purdy_initiatives_delete
DROP POLICY IF EXISTS "purdy_initiatives_delete" ON public.purdy_initiatives;
CREATE POLICY "purdy_initiatives_delete" ON public.purdy_initiatives
  AS PERMISSIVE
  FOR DELETE
  TO public
  USING ((created_by = (SELECT auth.uid())));

-- Table: purdy_initiatives, Policy: purdy_initiatives_insert
DROP POLICY IF EXISTS "purdy_initiatives_insert" ON public.purdy_initiatives;
CREATE POLICY "purdy_initiatives_insert" ON public.purdy_initiatives
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((created_by = (SELECT auth.uid())));

-- Table: purdy_initiatives, Policy: purdy_initiatives_select
DROP POLICY IF EXISTS "purdy_initiatives_select" ON public.purdy_initiatives;
CREATE POLICY "purdy_initiatives_select" ON public.purdy_initiatives
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
   FROM purdy_initiative_members
  WHERE ((purdy_initiative_members.initiative_id = purdy_initiatives.id) AND (purdy_initiative_members.user_id = (SELECT auth.uid())))))));

-- Table: purdy_initiatives, Policy: purdy_initiatives_update
DROP POLICY IF EXISTS "purdy_initiatives_update" ON public.purdy_initiatives;
CREATE POLICY "purdy_initiatives_update" ON public.purdy_initiatives
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
   FROM purdy_initiative_members
  WHERE ((purdy_initiative_members.initiative_id = purdy_initiatives.id) AND (purdy_initiative_members.user_id = (SELECT auth.uid())) AND (purdy_initiative_members.role = ANY (ARRAY['owner'::text, 'editor'::text])))))));

-- Table: purdy_messages, Policy: purdy_messages_insert
DROP POLICY IF EXISTS "purdy_messages_insert" ON public.purdy_messages;
CREATE POLICY "purdy_messages_insert" ON public.purdy_messages
  AS PERMISSIVE
  FOR INSERT
  TO public
  WITH CHECK ((EXISTS ( SELECT 1
   FROM purdy_conversations
  WHERE ((purdy_conversations.id = purdy_messages.conversation_id) AND (purdy_conversations.user_id = (SELECT auth.uid()))))));

-- Table: purdy_messages, Policy: purdy_messages_select
DROP POLICY IF EXISTS "purdy_messages_select" ON public.purdy_messages;
CREATE POLICY "purdy_messages_select" ON public.purdy_messages
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM purdy_conversations
  WHERE ((purdy_conversations.id = purdy_messages.conversation_id) AND (purdy_conversations.user_id = (SELECT auth.uid()))))));

-- Table: purdy_outputs, Policy: purdy_outputs_select
DROP POLICY IF EXISTS "purdy_outputs_select" ON public.purdy_outputs;
CREATE POLICY "purdy_outputs_select" ON public.purdy_outputs
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM purdy_initiatives
  WHERE ((purdy_initiatives.id = purdy_outputs.initiative_id) AND ((purdy_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM purdy_initiative_members
          WHERE ((purdy_initiative_members.initiative_id = purdy_initiatives.id) AND (purdy_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: purdy_runs, Policy: purdy_runs_select
DROP POLICY IF EXISTS "purdy_runs_select" ON public.purdy_runs;
CREATE POLICY "purdy_runs_select" ON public.purdy_runs
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM purdy_initiatives
  WHERE ((purdy_initiatives.id = purdy_runs.initiative_id) AND ((purdy_initiatives.created_by = (SELECT auth.uid())) OR (EXISTS ( SELECT 1
           FROM purdy_initiative_members
          WHERE ((purdy_initiative_members.initiative_id = purdy_initiatives.id) AND (purdy_initiative_members.user_id = (SELECT auth.uid()))))))))));

-- Table: research_schedule, Policy: Service role full access to research_schedule
DROP POLICY IF EXISTS "Service role full access to research_schedule" ON public.research_schedule;
CREATE POLICY "Service role full access to research_schedule" ON public.research_schedule
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: research_schedule, Policy: Users can view research schedules
DROP POLICY IF EXISTS "Users can view research schedules" ON public.research_schedule;
CREATE POLICY "Users can view research schedules" ON public.research_schedule
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))) OR (client_id IS NULL)));

-- Table: research_sources, Policy: Service role full access to research_sources
DROP POLICY IF EXISTS "Service role full access to research_sources" ON public.research_sources;
CREATE POLICY "Service role full access to research_sources" ON public.research_sources
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: research_tasks, Policy: Service role full access to research_tasks
DROP POLICY IF EXISTS "Service role full access to research_tasks" ON public.research_tasks;
CREATE POLICY "Service role full access to research_tasks" ON public.research_tasks
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: research_tasks, Policy: Users can view research tasks for their clients
DROP POLICY IF EXISTS "Users can view research tasks for their clients" ON public.research_tasks;
CREATE POLICY "Users can view research tasks for their clients" ON public.research_tasks
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))) OR (client_id IS NULL)));

-- Table: roi_opportunities, Policy: Users can manage ROI opportunities in their client
DROP POLICY IF EXISTS "Users can manage ROI opportunities in their client" ON public.roi_opportunities;
CREATE POLICY "Users can manage ROI opportunities in their client" ON public.roi_opportunities
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: roi_opportunities, Policy: Users can view ROI opportunities in their client
DROP POLICY IF EXISTS "Users can view ROI opportunities in their client" ON public.roi_opportunities;
CREATE POLICY "Users can view ROI opportunities in their client" ON public.roi_opportunities
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: stakeholder_candidates, Policy: Users can update stakeholder candidates in their client
DROP POLICY IF EXISTS "Users can update stakeholder candidates in their client" ON public.stakeholder_candidates;
CREATE POLICY "Users can update stakeholder candidates in their client" ON public.stakeholder_candidates
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: stakeholder_candidates, Policy: Users can view stakeholder candidates in their client
DROP POLICY IF EXISTS "Users can view stakeholder candidates in their client" ON public.stakeholder_candidates;
CREATE POLICY "Users can view stakeholder candidates in their client" ON public.stakeholder_candidates
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: stakeholder_insights, Policy: Users can manage insights for their stakeholders
DROP POLICY IF EXISTS "Users can manage insights for their stakeholders" ON public.stakeholder_insights;
CREATE POLICY "Users can manage insights for their stakeholders" ON public.stakeholder_insights
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((stakeholder_id IN ( SELECT s.id
   FROM (stakeholders s
     JOIN users u ON ((s.client_id = u.client_id)))
  WHERE (u.id = (SELECT auth.uid())))));

-- Table: stakeholder_insights, Policy: Users can view insights for their stakeholders
DROP POLICY IF EXISTS "Users can view insights for their stakeholders" ON public.stakeholder_insights;
CREATE POLICY "Users can view insights for their stakeholders" ON public.stakeholder_insights
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((stakeholder_id IN ( SELECT s.id
   FROM (stakeholders s
     JOIN users u ON ((s.client_id = u.client_id)))
  WHERE (u.id = (SELECT auth.uid())))));

-- Table: stakeholder_metrics, Policy: Service role has full access to stakeholder_metrics
DROP POLICY IF EXISTS "Service role has full access to stakeholder_metrics" ON public.stakeholder_metrics;
CREATE POLICY "Service role has full access to stakeholder_metrics" ON public.stakeholder_metrics
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: stakeholder_metrics, Policy: Users can manage metrics in their client
DROP POLICY IF EXISTS "Users can manage metrics in their client" ON public.stakeholder_metrics;
CREATE POLICY "Users can manage metrics in their client" ON public.stakeholder_metrics
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: stakeholder_metrics, Policy: Users can view metrics in their client
DROP POLICY IF EXISTS "Users can view metrics in their client" ON public.stakeholder_metrics;
CREATE POLICY "Users can view metrics in their client" ON public.stakeholder_metrics
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: stakeholders, Policy: Users can manage stakeholders in their client
DROP POLICY IF EXISTS "Users can manage stakeholders in their client" ON public.stakeholders;
CREATE POLICY "Users can manage stakeholders in their client" ON public.stakeholders
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: stakeholders, Policy: Users can view stakeholders in their client
DROP POLICY IF EXISTS "Users can view stakeholders in their client" ON public.stakeholders;
CREATE POLICY "Users can view stakeholders in their client" ON public.stakeholders
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: task_candidates, Policy: Users can update task candidates in their client
DROP POLICY IF EXISTS "Users can update task candidates in their client" ON public.task_candidates;
CREATE POLICY "Users can update task candidates in their client" ON public.task_candidates
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: task_candidates, Policy: Users can view task candidates in their client
DROP POLICY IF EXISTS "Users can view task candidates in their client" ON public.task_candidates;
CREATE POLICY "Users can view task candidates in their client" ON public.task_candidates
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((client_id IN ( SELECT users.client_id
   FROM users
  WHERE (users.id = (SELECT auth.uid())))));

-- Table: task_comments, Policy: Service role has full access to task_comments
DROP POLICY IF EXISTS "Service role has full access to task_comments" ON public.task_comments;
CREATE POLICY "Service role has full access to task_comments" ON public.task_comments
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: task_comments, Policy: Users can manage comments on accessible tasks
DROP POLICY IF EXISTS "Users can manage comments on accessible tasks" ON public.task_comments;
CREATE POLICY "Users can manage comments on accessible tasks" ON public.task_comments
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((task_id IN ( SELECT project_tasks.id
   FROM project_tasks
  WHERE (project_tasks.client_id IN ( SELECT users.client_id
           FROM users
          WHERE (users.id = (SELECT auth.uid())))))));

-- Table: task_comments, Policy: Users can view comments on accessible tasks
DROP POLICY IF EXISTS "Users can view comments on accessible tasks" ON public.task_comments;
CREATE POLICY "Users can view comments on accessible tasks" ON public.task_comments
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((task_id IN ( SELECT project_tasks.id
   FROM project_tasks
  WHERE (project_tasks.client_id IN ( SELECT users.client_id
           FROM users
          WHERE (users.id = (SELECT auth.uid())))))));

-- Table: task_history, Policy: Service role has full access to task_history
DROP POLICY IF EXISTS "Service role has full access to task_history" ON public.task_history;
CREATE POLICY "Service role has full access to task_history" ON public.task_history
  AS PERMISSIVE
  FOR ALL
  TO service_role
  USING (true);

-- Table: task_history, Policy: Users can view history on accessible tasks
DROP POLICY IF EXISTS "Users can view history on accessible tasks" ON public.task_history;
CREATE POLICY "Users can view history on accessible tasks" ON public.task_history
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((task_id IN ( SELECT project_tasks.id
   FROM project_tasks
  WHERE (project_tasks.client_id IN ( SELECT users.client_id
           FROM users
          WHERE (users.id = (SELECT auth.uid())))))));

-- Table: theme_settings, Policy: Admins can manage theme settings
DROP POLICY IF EXISTS "Admins can manage theme settings" ON public.theme_settings;
CREATE POLICY "Admins can manage theme settings" ON public.theme_settings
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((EXISTS ( SELECT 1
   FROM users
  WHERE ((users.id = (SELECT auth.uid())) AND ((users.role)::text = 'admin'::text) AND (users.client_id = theme_settings.client_id)))));

-- Table: theme_settings, Policy: Users can read theme settings
DROP POLICY IF EXISTS "Users can read theme settings" ON public.theme_settings;
CREATE POLICY "Users can read theme settings" ON public.theme_settings
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((EXISTS ( SELECT 1
   FROM users
  WHERE ((users.id = (SELECT auth.uid())) AND (users.client_id = theme_settings.client_id)))));

-- Table: user_quick_prompts, Policy: Users can manage own prompts
DROP POLICY IF EXISTS "Users can manage own prompts" ON public.user_quick_prompts;
CREATE POLICY "Users can manage own prompts" ON public.user_quick_prompts
  AS PERMISSIVE
  FOR ALL
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: user_quick_prompts, Policy: Users can view own prompts
DROP POLICY IF EXISTS "Users can view own prompts" ON public.user_quick_prompts;
CREATE POLICY "Users can view own prompts" ON public.user_quick_prompts
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING ((user_id = (SELECT auth.uid())));

-- Table: users, Policy: Users can update own profile
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile" ON public.users
  AS PERMISSIVE
  FOR UPDATE
  TO public
  USING (((SELECT auth.uid()) = id));

-- Table: users, Policy: Users can view own profile
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
CREATE POLICY "Users can view own profile" ON public.users
  AS PERMISSIVE
  FOR SELECT
  TO public
  USING (((SELECT auth.uid()) = id));

-- Total auth_rls_initplan policies fixed: 175

-- =============================================================
-- SECTION 2: Fix multiple_permissive_policies
-- Convert service_role policies to TO service_role,
-- drop redundant SELECT policies covered by FOR ALL
-- =============================================================

-- Total multiple_permissive fixes: 0 rewritten, 0 dropped

-- =============================================================
-- SECTION 3: Drop duplicate index
-- =============================================================

-- idx_docs_user_date duplicates idx_documents_uploaded_by_at
DROP INDEX IF EXISTS idx_docs_user_date;

-- =============================================================
-- SECTION 4: Create missing indexes for foreign keys
-- =============================================================

CREATE INDEX IF NOT EXISTS idx_agent_instruction_versions_created_by ON public.agent_instruction_versions (created_by);
CREATE INDEX IF NOT EXISTS idx_agent_knowledge_base_added_by ON public.agent_knowledge_base (added_by);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_client_id ON public.api_usage_logs (client_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_user_id ON public.api_usage_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_agent_instruction_version_id ON public.conversations (agent_instruction_version_id);
CREATE INDEX IF NOT EXISTS idx_disco_bundles_source_output_id ON public.disco_bundles (source_output_id);
CREATE INDEX IF NOT EXISTS idx_disco_conversations_initiative_id ON public.disco_conversations (initiative_id);
CREATE INDEX IF NOT EXISTS idx_disco_conversations_user_id ON public.disco_conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_disco_document_chunks_document_id ON public.disco_document_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_disco_initiatives_created_by ON public.disco_initiatives (created_by);
CREATE INDEX IF NOT EXISTS idx_disco_initiatives_sponsor_stakeholder_id ON public.disco_initiatives (sponsor_stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_disco_messages_conversation_id ON public.disco_messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_disco_outputs_run_id ON public.disco_outputs (run_id);
CREATE INDEX IF NOT EXISTS idx_disco_prds_source_output_id ON public.disco_prds (source_output_id);
CREATE INDEX IF NOT EXISTS idx_disco_run_documents_document_id ON public.disco_run_documents (document_id);
CREATE INDEX IF NOT EXISTS idx_disco_runs_run_by ON public.disco_runs (run_by);
CREATE INDEX IF NOT EXISTS idx_disco_system_kb_chunks_kb_id ON public.disco_system_kb_chunks (kb_id);
CREATE INDEX IF NOT EXISTS idx_document_classifications_reviewed_by ON public.document_classifications (reviewed_by);
CREATE INDEX IF NOT EXISTS idx_glean_connector_requests_connector_id ON public.glean_connector_requests (connector_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_resolution_task_id ON public.knowledge_gaps (resolution_task_id);
CREATE INDEX IF NOT EXISTS idx_meeting_transcripts_document_id ON public.meeting_transcripts (document_id);
CREATE INDEX IF NOT EXISTS idx_oauth_states_user_id ON public.oauth_states (user_id);
CREATE INDEX IF NOT EXISTS idx_project_candidates_created_project_id ON public.project_candidates (created_project_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_created_by ON public.project_tasks (created_by);
CREATE INDEX IF NOT EXISTS idx_project_tasks_related_project_id ON public.project_tasks (related_project_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_source_disco_output_id ON public.project_tasks (source_disco_output_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_source_initiative_id ON public.project_tasks (source_initiative_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_source_project_id ON public.project_tasks (source_project_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_updated_by ON public.project_tasks (updated_by);
CREATE INDEX IF NOT EXISTS idx_purdy_conversations_initiative_id ON public.purdy_conversations (initiative_id);
CREATE INDEX IF NOT EXISTS idx_purdy_conversations_user_id ON public.purdy_conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_purdy_document_chunks_document_id ON public.purdy_document_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_purdy_initiatives_created_by ON public.purdy_initiatives (created_by);
CREATE INDEX IF NOT EXISTS idx_purdy_messages_conversation_id ON public.purdy_messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_purdy_outputs_run_id ON public.purdy_outputs (run_id);
CREATE INDEX IF NOT EXISTS idx_purdy_run_documents_document_id ON public.purdy_run_documents (document_id);
CREATE INDEX IF NOT EXISTS idx_purdy_runs_run_by ON public.purdy_runs (run_by);
CREATE INDEX IF NOT EXISTS idx_purdy_system_kb_chunks_kb_id ON public.purdy_system_kb_chunks (kb_id);
CREATE INDEX IF NOT EXISTS idx_research_tasks_result_document_id ON public.research_tasks (result_document_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_created_stakeholder_id ON public.stakeholder_candidates (created_stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_merged_into_stakeholder_id ON public.stakeholder_candidates (merged_into_stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_insights_source_document_id ON public.stakeholder_insights (source_document_id);
CREATE INDEX IF NOT EXISTS idx_stakeholders_reports_to ON public.stakeholders (reports_to);
CREATE INDEX IF NOT EXISTS idx_task_candidates_created_task_id ON public.task_candidates (created_task_id);
CREATE INDEX IF NOT EXISTS idx_task_history_user_id ON public.task_history (user_id);

-- Total FK indexes created: 45

-- =============================================================
-- SECTION 5: Drop unused indexes (0 scans since last stats reset)
-- Excludes: primary keys, unique constraints, embedding/vector indexes
-- =============================================================

-- KEPT (safelist): idx_disco_chunks_embedding (18440 KB)
-- KEPT (safelist): help_chunks_embedding_idx (7696 KB)
-- KEPT (safelist): idx_task_candidates_embedding (1760 KB)
-- KEPT (safelist): idx_project_tasks_embedding (1608 KB)
-- KEPT (safelist): idx_purdy_chunks_embedding (1608 KB)
-- KEPT (safelist): idx_purdy_system_kb_embedding (1608 KB)
DROP INDEX IF EXISTS idx_obsidian_sync_log_started_at;  -- obsidian_sync_log (368 KB)
DROP INDEX IF EXISTS idx_document_tags_tag;  -- document_tags (288 KB)
-- KEPT (safelist): idx_documents_uploaded_by_at (160 KB)
-- KEPT (covers FK): idx_obsidian_sync_log_user_id (104 KB)
-- KEPT (covers FK): idx_obsidian_sync_log_config_id (104 KB)
DROP INDEX IF EXISTS idx_project_candidates_pending;  -- project_candidates (88 KB)
-- KEPT (covers FK): idx_documents_user_id (80 KB)
-- KEPT (covers FK): idx_obsidian_sync_state_config_id (72 KB)
DROP INDEX IF EXISTS idx_documents_document_type;  -- documents (72 KB)
-- KEPT (covers FK): idx_documents_client_id (72 KB)
DROP INDEX IF EXISTS idx_documents_projects_scanned_at;  -- documents (64 KB)
DROP INDEX IF EXISTS idx_documents_tasks_scanned_at;  -- documents (64 KB)
DROP INDEX IF EXISTS idx_project_candidates_status_date;  -- project_candidates (64 KB)
DROP INDEX IF EXISTS idx_task_candidates_status_date;  -- task_candidates (56 KB)
DROP INDEX IF EXISTS idx_documents_stakeholders_scanned_at;  -- documents (56 KB)
DROP INDEX IF EXISTS idx_obsidian_sync_state_status;  -- obsidian_sync_state (56 KB)
DROP INDEX IF EXISTS help_chunks_role_access_idx;  -- help_chunks (40 KB)
DROP INDEX IF EXISTS idx_project_candidates_document;  -- project_candidates (40 KB)
DROP INDEX IF EXISTS idx_help_chunks_created_at;  -- help_chunks (40 KB)
DROP INDEX IF EXISTS idx_task_candidates_document;  -- task_candidates (40 KB)
DROP INDEX IF EXISTS idx_disco_chunks_initiative;  -- disco_document_chunks (32 KB)
DROP INDEX IF EXISTS idx_messages_metadata_image_suggestion;  -- messages (24 KB)
DROP INDEX IF EXISTS idx_disco_outputs_initiative;  -- disco_outputs (16 KB)
DROP INDEX IF EXISTS idx_disco_outputs_synthesis_mode;  -- disco_outputs (16 KB)
DROP INDEX IF EXISTS idx_disco_outputs_format;  -- disco_outputs (16 KB)
DROP INDEX IF EXISTS idx_message_documents_created_at;  -- message_documents (16 KB)
DROP INDEX IF EXISTS idx_disco_initiative_folders_path;  -- disco_initiative_folders (16 KB)
-- KEPT (covers FK): idx_message_documents_document_id (16 KB)
-- KEPT (covers FK): idx_message_documents_message_id (16 KB)
DROP INDEX IF EXISTS idx_conversations_client_project;  -- conversations (16 KB)
DROP INDEX IF EXISTS idx_conversations_client_initiative;  -- conversations (16 KB)
DROP INDEX IF EXISTS idx_google_drive_sync_log_status;  -- google_drive_sync_log (16 KB)
-- KEPT (covers FK): idx_google_drive_sync_log_user_id (16 KB)
-- KEPT (covers FK): idx_conversations_client_id (16 KB)
DROP INDEX IF EXISTS idx_graph_sync_log_client;  -- graph_sync_log (16 KB)
DROP INDEX IF EXISTS idx_graph_sync_log_entity;  -- graph_sync_log (16 KB)
DROP INDEX IF EXISTS idx_graph_sync_log_status;  -- graph_sync_log (16 KB)
DROP INDEX IF EXISTS idx_agents_is_active;  -- agents (16 KB)
DROP INDEX IF EXISTS help_conversations_help_type_idx;  -- help_conversations (16 KB)
DROP INDEX IF EXISTS help_conversations_user_id_idx;  -- help_conversations (16 KB)
DROP INDEX IF EXISTS idx_engagement_history_client;  -- engagement_level_history (16 KB)
DROP INDEX IF EXISTS idx_graph_sync_state_client;  -- graph_sync_state (16 KB)
DROP INDEX IF EXISTS idx_meeting_room_participants_meeting_id;  -- meeting_room_participants (16 KB)
-- KEPT (covers FK): idx_meeting_room_participants_agent_id (16 KB)
-- KEPT (covers FK): idx_project_conversations_project_id (16 KB)
-- KEPT (covers FK): idx_project_conversations_client_id (16 KB)
DROP INDEX IF EXISTS idx_project_conversations_user_id;  -- project_conversations (16 KB)
DROP INDEX IF EXISTS idx_project_conversations_created_at;  -- project_conversations (16 KB)
DROP INDEX IF EXISTS idx_stakeholder_candidates_pending;  -- stakeholder_candidates (16 KB)
DROP INDEX IF EXISTS idx_stakeholder_candidates_document;  -- stakeholder_candidates (16 KB)
DROP INDEX IF EXISTS idx_stakeholder_candidates_status_date;  -- stakeholder_candidates (16 KB)
DROP INDEX IF EXISTS idx_stakeholder_candidates_match;  -- stakeholder_candidates (16 KB)
DROP INDEX IF EXISTS idx_stakeholder_candidates_matched_candidate;  -- stakeholder_candidates (16 KB)
DROP INDEX IF EXISTS idx_project_candidates_match;  -- project_candidates (16 KB)
DROP INDEX IF EXISTS idx_opportunity_candidates_matched_candidate;  -- project_candidates (16 KB)
DROP INDEX IF EXISTS idx_research_tasks_status;  -- research_tasks (16 KB)
DROP INDEX IF EXISTS idx_research_tasks_client;  -- research_tasks (16 KB)
DROP INDEX IF EXISTS idx_research_tasks_focus_area;  -- research_tasks (16 KB)
DROP INDEX IF EXISTS idx_research_tasks_created;  -- research_tasks (16 KB)
DROP INDEX IF EXISTS idx_research_tasks_type;  -- research_tasks (16 KB)
DROP INDEX IF EXISTS idx_research_schedule_active;  -- research_schedule (16 KB)
DROP INDEX IF EXISTS idx_research_sources_domain;  -- research_sources (16 KB)
DROP INDEX IF EXISTS idx_research_sources_tier;  -- research_sources (16 KB)
DROP INDEX IF EXISTS idx_engagement_history_level;  -- engagement_level_history (16 KB)
DROP INDEX IF EXISTS idx_engagement_history_client_time;  -- engagement_level_history (16 KB)
DROP INDEX IF EXISTS idx_engagement_history_level_change;  -- engagement_level_history (16 KB)
DROP INDEX IF EXISTS idx_compass_reports_user_date;  -- compass_status_reports (16 KB)
DROP INDEX IF EXISTS idx_agent_topic_mapping_topic;  -- agent_topic_mapping (16 KB)
DROP INDEX IF EXISTS idx_agent_topic_mapping_agent;  -- agent_topic_mapping (16 KB)
DROP INDEX IF EXISTS idx_agent_kb_agent_id;  -- agent_knowledge_base (16 KB)
DROP INDEX IF EXISTS idx_stakeholders_priority_level;  -- stakeholders (16 KB)
DROP INDEX IF EXISTS idx_stakeholders_relationship_status;  -- stakeholders (16 KB)
-- KEPT (covers FK): idx_stakeholders_client_id (16 KB)
DROP INDEX IF EXISTS idx_stakeholders_department;  -- stakeholders (16 KB)
DROP INDEX IF EXISTS idx_stakeholders_engagement_level;  -- stakeholders (16 KB)
DROP INDEX IF EXISTS idx_stakeholders_last_interaction;  -- stakeholders (16 KB)
DROP INDEX IF EXISTS idx_stakeholders_name;  -- stakeholders (16 KB)
-- KEPT (covers FK): idx_stakeholder_metrics_client_id (16 KB)
DROP INDEX IF EXISTS idx_stakeholder_metrics_validation;  -- stakeholder_metrics (16 KB)
DROP INDEX IF EXISTS idx_stakeholder_metrics_needs_validation;  -- stakeholder_metrics (16 KB)
-- KEPT (covers FK): idx_obsidian_vault_configs_client_id (16 KB)
DROP INDEX IF EXISTS idx_agent_kb_document_id;  -- agent_knowledge_base (16 KB)
DROP INDEX IF EXISTS idx_agent_kb_priority;  -- agent_knowledge_base (16 KB)
DROP INDEX IF EXISTS idx_documents_granola_unscanned;  -- documents (16 KB)
DROP INDEX IF EXISTS idx_documents_needs_reverse_sync;  -- documents (16 KB)
-- KEPT (covers FK): idx_ai_projects_client_id (16 KB)
DROP INDEX IF EXISTS idx_ai_projects_code;  -- ai_projects (16 KB)
DROP INDEX IF EXISTS idx_ai_projects_department;  -- ai_projects (16 KB)
DROP INDEX IF EXISTS idx_ai_projects_tier;  -- ai_projects (16 KB)
DROP INDEX IF EXISTS idx_ai_projects_client_tier_status;  -- ai_projects (16 KB)
DROP INDEX IF EXISTS idx_ai_opportunities_project_name;  -- ai_projects (16 KB)
DROP INDEX IF EXISTS idx_ai_projects_scoring_confidence;  -- ai_projects (16 KB)
DROP INDEX IF EXISTS idx_ai_opportunities_goal_alignment;  -- ai_projects (16 KB)
-- KEPT (covers FK): idx_task_history_task_id (16 KB)
DROP INDEX IF EXISTS idx_task_history_created_at;  -- task_history (16 KB)
-- KEPT (covers FK): idx_project_tasks_client_id (16 KB)
DROP INDEX IF EXISTS idx_project_tasks_status;  -- project_tasks (16 KB)
DROP INDEX IF EXISTS idx_project_tasks_assignee_user;  -- project_tasks (16 KB)
DROP INDEX IF EXISTS idx_project_tasks_priority;  -- project_tasks (16 KB)
DROP INDEX IF EXISTS idx_project_tasks_client_status;  -- project_tasks (16 KB)
DROP INDEX IF EXISTS idx_project_tasks_client_status_due;  -- project_tasks (16 KB)
-- KEPT (covers FK): idx_conversations_user_id (16 KB)
-- KEPT (covers FK): idx_theme_settings_client_id (16 KB)
DROP INDEX IF EXISTS idx_agent_kb_relevance;  -- agent_knowledge_base (16 KB)
DROP INDEX IF EXISTS idx_compass_reports_client;  -- compass_status_reports (16 KB)
DROP INDEX IF EXISTS idx_task_candidates_linked_project;  -- task_candidates (16 KB)
DROP INDEX IF EXISTS idx_task_candidates_source_project;  -- task_candidates (16 KB)
DROP INDEX IF EXISTS idx_disco_bundles_status;  -- disco_bundles (16 KB)
DROP INDEX IF EXISTS idx_task_candidates_matched_candidate;  -- task_candidates (16 KB)
DROP INDEX IF EXISTS idx_task_candidates_linked_project_candidate;  -- task_candidates (16 KB)
DROP INDEX IF EXISTS idx_disco_bundles_created;  -- disco_bundles (16 KB)
DROP INDEX IF EXISTS idx_disco_initiatives_status_dates;  -- disco_initiatives (16 KB)
DROP INDEX IF EXISTS idx_disco_initiatives_goal_alignment_score;  -- disco_initiatives (16 KB)
-- KEPT (covers FK): idx_conversations_agent_id (16 KB)
DROP INDEX IF EXISTS idx_conversations_agent_updated;  -- conversations (16 KB)
DROP INDEX IF EXISTS idx_agent_instructions_is_active;  -- agent_instruction_versions (16 KB)
DROP INDEX IF EXISTS idx_users_avatar_url;  -- users (16 KB)
-- KEPT (covers FK): idx_users_client_id (16 KB)
DROP INDEX IF EXISTS idx_users_email;  -- users (16 KB)
DROP INDEX IF EXISTS idx_glean_connectors_contentful_status;  -- glean_connectors (16 KB)
DROP INDEX IF EXISTS idx_glean_connectors_type;  -- glean_connectors (16 KB)
DROP INDEX IF EXISTS idx_glean_connectors_category;  -- glean_connectors (16 KB)
DROP INDEX IF EXISTS idx_glean_connectors_disco_score;  -- glean_connectors (16 KB)
DROP INDEX IF EXISTS idx_disco_init_docs_linked_at;  -- disco_initiative_documents (16 KB)
DROP INDEX IF EXISTS idx_disco_checkpoints_status;  -- disco_checkpoints (16 KB)
-- KEPT (covers FK): idx_meeting_rooms_client_id (16 KB)
-- KEPT (covers FK): idx_meeting_rooms_user_id (16 KB)
DROP INDEX IF EXISTS idx_meeting_rooms_status;  -- meeting_rooms (16 KB)
DROP INDEX IF EXISTS idx_meeting_rooms_created_at;  -- meeting_rooms (16 KB)
-- KEPT (covers FK): idx_conversations_project_id (16 KB)
-- KEPT (covers FK): idx_conversations_initiative_id (16 KB)
DROP INDEX IF EXISTS idx_glean_connector_requests_priority;  -- glean_connector_requests (8 KB)
DROP INDEX IF EXISTS idx_google_tokens_next_sync;  -- google_drive_tokens (8 KB)
-- KEPT (covers FK): idx_user_quick_prompts_user_id (8 KB)
DROP INDEX IF EXISTS idx_doc_class_needs_review;  -- document_classifications (8 KB)
DROP INDEX IF EXISTS idx_help_messages_feedback;  -- help_messages (8 KB)
DROP INDEX IF EXISTS idx_stakeholder_insights_is_resolved;  -- stakeholder_insights (8 KB)
DROP INDEX IF EXISTS idx_stakeholder_insights_transcript_id;  -- stakeholder_insights (8 KB)
-- KEPT (covers FK): idx_meeting_transcripts_user_id (8 KB)
DROP INDEX IF EXISTS idx_meeting_transcripts_meeting_date;  -- meeting_transcripts (8 KB)
DROP INDEX IF EXISTS idx_meeting_transcripts_status;  -- meeting_transcripts (8 KB)
DROP INDEX IF EXISTS idx_roi_opportunities_status;  -- roi_opportunities (8 KB)
DROP INDEX IF EXISTS idx_roi_opportunities_department;  -- roi_opportunities (8 KB)
DROP INDEX IF EXISTS idx_agent_handoffs_from_agent;  -- agent_handoffs (8 KB)
DROP INDEX IF EXISTS idx_agent_handoffs_to_agent;  -- agent_handoffs (8 KB)
DROP INDEX IF EXISTS idx_disco_bundle_feedback_bundle;  -- disco_bundle_feedback (8 KB)
DROP INDEX IF EXISTS idx_disco_bundle_feedback_user;  -- disco_bundle_feedback (8 KB)
DROP INDEX IF EXISTS idx_disco_prds_bundle;  -- disco_prds (8 KB)
DROP INDEX IF EXISTS idx_disco_prds_status;  -- disco_prds (8 KB)
DROP INDEX IF EXISTS idx_knowledge_gaps_status;  -- knowledge_gaps (8 KB)
DROP INDEX IF EXISTS idx_knowledge_gaps_client;  -- knowledge_gaps (8 KB)
DROP INDEX IF EXISTS idx_knowledge_gaps_agent;  -- knowledge_gaps (8 KB)
DROP INDEX IF EXISTS idx_knowledge_gaps_priority;  -- knowledge_gaps (8 KB)
DROP INDEX IF EXISTS idx_project_stakeholder_link_role;  -- project_stakeholder_link (8 KB)
DROP INDEX IF EXISTS idx_documents_external_id;  -- documents (8 KB)
DROP INDEX IF EXISTS idx_documents_google_drive_file_id;  -- documents (8 KB)
-- KEPT (covers FK): idx_task_comments_user_id (8 KB)
DROP INDEX IF EXISTS idx_project_tasks_source_transcript;  -- project_tasks (8 KB)
DROP INDEX IF EXISTS idx_project_tasks_source_research;  -- project_tasks (8 KB)
DROP INDEX IF EXISTS idx_task_candidates_matched_task;  -- task_candidates (8 KB)
DROP INDEX IF EXISTS idx_disco_initiatives_decided_at;  -- disco_initiatives (8 KB)
DROP INDEX IF EXISTS idx_purdy_members_initiative;  -- purdy_initiative_members (8 KB)
DROP INDEX IF EXISTS idx_purdy_members_user;  -- purdy_initiative_members (8 KB)
DROP INDEX IF EXISTS idx_purdy_docs_initiative;  -- purdy_documents (8 KB)
DROP INDEX IF EXISTS idx_purdy_chunks_initiative;  -- purdy_document_chunks (8 KB)
DROP INDEX IF EXISTS idx_purdy_runs_initiative;  -- purdy_runs (8 KB)
DROP INDEX IF EXISTS idx_purdy_outputs_initiative;  -- purdy_outputs (8 KB)
-- KEPT (covers FK): idx_meeting_rooms_project_id (8 KB)
-- KEPT (covers FK): idx_meeting_rooms_initiative_id (8 KB)
DROP INDEX IF EXISTS idx_disco_outputs_stakeholder_rating;  -- disco_outputs (8 KB)
DROP INDEX IF EXISTS idx_glean_connector_requests_status;  -- glean_connector_requests (8 KB)
DROP INDEX IF EXISTS idx_api_usage_operation;  -- api_usage_logs (8 KB)

-- Total unused indexes dropped: 140, kept: 38

-- =============================================================
-- Reload PostgREST schema cache
-- =============================================================
NOTIFY pgrst, 'reload schema';

COMMIT;
-- Migration 080b: Fix remaining multiple_permissive and unindexed FK issues
BEGIN;

-- SECTION 1: Drop redundant SELECT policies covered by FOR ALL

-- ai_projects: "Users can view projects in their client" redundant with "Users can manage projects in their client"
DROP POLICY IF EXISTS "Users can view projects in their client" ON public.ai_projects;

-- meeting_room_participants: "Users can view participants in their meetings" redundant with "Users can manage participants in their meetings"
DROP POLICY IF EXISTS "Users can view participants in their meetings" ON public.meeting_room_participants;

-- meeting_transcripts: "Users can view their transcripts" redundant with "Users can manage their transcripts"
DROP POLICY IF EXISTS "Users can view their transcripts" ON public.meeting_transcripts;

-- obsidian_sync_log: "Users can view their own sync logs" redundant with "Users can manage their own sync logs"
DROP POLICY IF EXISTS "Users can view their own sync logs" ON public.obsidian_sync_log;

-- obsidian_sync_state: "Users can view sync state for their configs" redundant with "Users can manage sync state for their configs"
DROP POLICY IF EXISTS "Users can view sync state for their configs" ON public.obsidian_sync_state;

-- obsidian_vault_configs: "Users can view their own vault configs" redundant with "Users can manage their own vault configs"
DROP POLICY IF EXISTS "Users can view their own vault configs" ON public.obsidian_vault_configs;

-- project_stakeholder_link: "Users can view project stakeholder links" redundant with "Users can manage project stakeholder links"
DROP POLICY IF EXISTS "Users can view project stakeholder links" ON public.project_stakeholder_link;

-- project_tasks: "Users can view tasks in their client" redundant with "Users can manage tasks in their client"
DROP POLICY IF EXISTS "Users can view tasks in their client" ON public.project_tasks;

-- roi_opportunities: "Users can view ROI opportunities in their client" redundant with "Users can manage ROI opportunities in their client"
DROP POLICY IF EXISTS "Users can view ROI opportunities in their client" ON public.roi_opportunities;

-- stakeholder_insights: "Users can view insights for their stakeholders" redundant with "Users can manage insights for their stakeholders"
DROP POLICY IF EXISTS "Users can view insights for their stakeholders" ON public.stakeholder_insights;

-- stakeholder_metrics: "Users can view metrics in their client" redundant with "Users can manage metrics in their client"
DROP POLICY IF EXISTS "Users can view metrics in their client" ON public.stakeholder_metrics;

-- stakeholders: "Users can view stakeholders in their client" redundant with "Users can manage stakeholders in their client"
DROP POLICY IF EXISTS "Users can view stakeholders in their client" ON public.stakeholders;

-- task_comments: "Users can view comments on accessible tasks" redundant with "Users can manage comments on accessible tasks"
DROP POLICY IF EXISTS "Users can view comments on accessible tasks" ON public.task_comments;

-- user_quick_prompts: "Users can view own prompts" redundant with "Users can manage own prompts"
DROP POLICY IF EXISTS "Users can view own prompts" ON public.user_quick_prompts;

-- Dropped 14 redundant SELECT policies

-- SECTION 2: Create missing FK indexes (post-080 cleanup)

CREATE INDEX IF NOT EXISTS idx_agent_handoffs_from_agent_id ON public.agent_handoffs (from_agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_handoffs_to_agent_id ON public.agent_handoffs (to_agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_knowledge_base_document_id ON public.agent_knowledge_base (document_id);
CREATE INDEX IF NOT EXISTS idx_compass_status_reports_client_id ON public.compass_status_reports (client_id);
CREATE INDEX IF NOT EXISTS idx_compass_status_reports_user_id ON public.compass_status_reports (user_id);
CREATE INDEX IF NOT EXISTS idx_disco_bundle_feedback_bundle_id ON public.disco_bundle_feedback (bundle_id);
CREATE INDEX IF NOT EXISTS idx_disco_bundle_feedback_user_id ON public.disco_bundle_feedback (user_id);
CREATE INDEX IF NOT EXISTS idx_disco_bundles_approved_by ON public.disco_bundles (approved_by);
CREATE INDEX IF NOT EXISTS idx_disco_checkpoints_approved_by ON public.disco_checkpoints (approved_by);
CREATE INDEX IF NOT EXISTS idx_disco_initiative_documents_linked_by ON public.disco_initiative_documents (linked_by);
CREATE INDEX IF NOT EXISTS idx_disco_initiative_folders_linked_by ON public.disco_initiative_folders (linked_by);
CREATE INDEX IF NOT EXISTS idx_disco_prds_approved_by ON public.disco_prds (approved_by);
CREATE INDEX IF NOT EXISTS idx_disco_prds_bundle_id ON public.disco_prds (bundle_id);
CREATE INDEX IF NOT EXISTS idx_engagement_level_history_client_id ON public.engagement_level_history (client_id);
CREATE INDEX IF NOT EXISTS idx_graph_sync_log_client_id ON public.graph_sync_log (client_id);
CREATE INDEX IF NOT EXISTS idx_help_conversations_user_id ON public.help_conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_client_id ON public.knowledge_gaps (client_id);
CREATE INDEX IF NOT EXISTS idx_project_candidates_accepted_by ON public.project_candidates (accepted_by);
CREATE INDEX IF NOT EXISTS idx_project_candidates_client_id ON public.project_candidates (client_id);
CREATE INDEX IF NOT EXISTS idx_project_candidates_matched_candidate_id ON public.project_candidates (matched_candidate_id);
CREATE INDEX IF NOT EXISTS idx_project_candidates_matched_project_id ON public.project_candidates (matched_project_id);
CREATE INDEX IF NOT EXISTS idx_project_candidates_rejected_by ON public.project_candidates (rejected_by);
CREATE INDEX IF NOT EXISTS idx_project_candidates_source_document_id ON public.project_candidates (source_document_id);
CREATE INDEX IF NOT EXISTS idx_project_conversations_user_id ON public.project_conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_project_documents_linked_by ON public.project_documents (linked_by);
CREATE INDEX IF NOT EXISTS idx_project_tasks_assignee_user_id ON public.project_tasks (assignee_user_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_source_research_task_id ON public.project_tasks (source_research_task_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_source_transcript_id ON public.project_tasks (source_transcript_id);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects (user_id);
CREATE INDEX IF NOT EXISTS idx_purdy_documents_initiative_id ON public.purdy_documents (initiative_id);
CREATE INDEX IF NOT EXISTS idx_purdy_initiative_members_user_id ON public.purdy_initiative_members (user_id);
CREATE INDEX IF NOT EXISTS idx_purdy_runs_initiative_id ON public.purdy_runs (initiative_id);
CREATE INDEX IF NOT EXISTS idx_research_tasks_client_id ON public.research_tasks (client_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_accepted_by ON public.stakeholder_candidates (accepted_by);
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_client_id ON public.stakeholder_candidates (client_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_matched_candidate_id ON public.stakeholder_candidates (matched_candidate_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_potential_match_stakeholder_id ON public.stakeholder_candidates (potential_match_stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_candidates_source_document_id ON public.stakeholder_candidates (source_document_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_insights_meeting_transcript_id ON public.stakeholder_insights (meeting_transcript_id);
CREATE INDEX IF NOT EXISTS idx_task_candidates_accepted_by ON public.task_candidates (accepted_by);
CREATE INDEX IF NOT EXISTS idx_task_candidates_linked_project_candidate_id ON public.task_candidates (linked_project_candidate_id);
CREATE INDEX IF NOT EXISTS idx_task_candidates_linked_project_id ON public.task_candidates (linked_project_id);
CREATE INDEX IF NOT EXISTS idx_task_candidates_matched_candidate_id ON public.task_candidates (matched_candidate_id);
CREATE INDEX IF NOT EXISTS idx_task_candidates_matched_task_id ON public.task_candidates (matched_task_id);
CREATE INDEX IF NOT EXISTS idx_task_candidates_rejected_by ON public.task_candidates (rejected_by);
CREATE INDEX IF NOT EXISTS idx_task_candidates_source_document_id ON public.task_candidates (source_document_id);
CREATE INDEX IF NOT EXISTS idx_task_candidates_source_project_id ON public.task_candidates (source_project_id);
CREATE INDEX IF NOT EXISTS idx_task_candidates_user_id ON public.task_candidates (user_id);

-- Created 48 FK indexes

-- =============================================================
-- SECTION 6: Fix search_path on SECURITY INVOKER functions
-- Migration 079 set search_path = '' on ALL functions, but only
-- SECURITY DEFINER functions need that. INVOKER functions need
-- search_path = public to find tables.
-- =============================================================

ALTER FUNCTION public.calculate_disco_integration_score SET search_path = public;
ALTER FUNCTION public.check_disco_integration_feasibility SET search_path = public;
ALTER FUNCTION public.compute_obsidian_sync_duration SET search_path = public;
ALTER FUNCTION public.copy_project_link_on_task_accept SET search_path = public;
ALTER FUNCTION public.count_conversation_images SET search_path = public;
ALTER FUNCTION public.count_recent_suggestions SET search_path = public;
ALTER FUNCTION public.get_agents_for_topic SET search_path = public;
ALTER FUNCTION public.get_priority_knowledge_gaps SET search_path = public;
ALTER FUNCTION public.get_todays_research_schedule SET search_path = public;
ALTER FUNCTION public.increment_gap_occurrence SET search_path = public;
ALTER FUNCTION public.log_connector_request SET search_path = public;
ALTER FUNCTION public.match_disco_all_chunks SET search_path = public;
ALTER FUNCTION public.match_disco_document_chunks SET search_path = public;
ALTER FUNCTION public.match_disco_system_kb_chunks SET search_path = public;
ALTER FUNCTION public.match_document_chunks SET search_path = public;
ALTER FUNCTION public.match_document_chunks_by_ids SET search_path = public;
ALTER FUNCTION public.match_document_chunks_by_type SET search_path = public;
ALTER FUNCTION public.match_document_chunks_with_agent_filter SET search_path = public;
ALTER FUNCTION public.match_help_chunks SET search_path = public;
ALTER FUNCTION public.match_purdy_all_chunks SET search_path = public;
ALTER FUNCTION public.match_purdy_document_chunks SET search_path = public;
ALTER FUNCTION public.match_purdy_system_kb_chunks SET search_path = public;
ALTER FUNCTION public.record_task_history SET search_path = public;
ALTER FUNCTION public.sync_document_tags_cache SET search_path = public;
ALTER FUNCTION public.update_compass_reports_updated_at SET search_path = public;
ALTER FUNCTION public.update_disco_checkpoint_timestamp SET search_path = public;
ALTER FUNCTION public.update_disco_initiatives_updated_at SET search_path = public;
ALTER FUNCTION public.update_disco_updated_at SET search_path = public;
ALTER FUNCTION public.update_graph_sync_state SET search_path = public;
ALTER FUNCTION public.update_meeting_rooms_updated_at SET search_path = public;
ALTER FUNCTION public.update_obsidian_sync_state_timestamp SET search_path = public;
ALTER FUNCTION public.update_obsidian_vault_config_timestamp SET search_path = public;
ALTER FUNCTION public.update_project_candidate_timestamp SET search_path = public;
ALTER FUNCTION public.update_project_task_timestamp SET search_path = public;
ALTER FUNCTION public.update_project_timestamp SET search_path = public;
ALTER FUNCTION public.update_purdy_initiatives_updated_at SET search_path = public;
ALTER FUNCTION public.update_stakeholder_interactions SET search_path = public;
ALTER FUNCTION public.update_stakeholder_metrics_timestamp SET search_path = public;
ALTER FUNCTION public.update_stakeholder_sentiment SET search_path = public;
ALTER FUNCTION public.update_system_instruction_versions_updated_at SET search_path = public;
ALTER FUNCTION public.update_task_comment_timestamp SET search_path = public;

NOTIFY pgrst, 'reload schema';
COMMIT;
