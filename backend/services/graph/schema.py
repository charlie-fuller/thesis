"""Neo4j Graph Schema Initialization.

Defines and creates the graph schema including:
- Node constraints and indexes
- Relationship types
- Initial schema validation
"""

import logging

from .connection import Neo4jConnection

logger = logging.getLogger(__name__)


# Schema definition - Comprehensive node types for full platform coverage
SCHEMA_CONSTRAINTS = [
    # Core entities - unique ID constraints
    ("Client", "id", "client_id_unique"),
    ("User", "id", "user_id_unique"),
    ("Agent", "id", "agent_id_unique"),
    ("Document", "id", "document_id_unique"),
    ("Chunk", "id", "chunk_id_unique"),
    ("Conversation", "id", "conversation_id_unique"),
    ("Message", "id", "message_id_unique"),
    ("Meeting", "id", "meeting_id_unique"),
    ("MeetingRoom", "id", "meeting_room_id_unique"),
    ("MeetingRoomMessage", "id", "meeting_room_message_id_unique"),
    ("Stakeholder", "id", "stakeholder_id_unique"),
    ("Insight", "id", "insight_id_unique"),
    ("ROIOpportunity", "id", "roi_opportunity_id_unique"),
    ("AgentInstruction", "id", "agent_instruction_id_unique"),
    # Inferred entities
    ("Concept", "name", "concept_name_unique"),
    ("Concern", "id", "concern_id_unique"),
    ("ActionItem", "id", "action_item_id_unique"),
    ("Expertise", "name", "expertise_name_unique"),
    ("Cluster", "name", "cluster_name_unique"),
]

SCHEMA_INDEXES = [
    # Multi-tenant isolation indexes (client_id on all tenant-scoped entities)
    ("Client", "name", "client_name_idx"),
    ("User", "client_id", "user_client_idx"),
    ("User", "email", "user_email_idx"),
    ("Document", "client_id", "document_client_idx"),
    ("Document", "filename", "document_filename_idx"),
    ("Document", "is_core_document", "document_core_idx"),
    ("Chunk", "document_id", "chunk_document_idx"),
    ("Conversation", "client_id", "conversation_client_idx"),
    ("Conversation", "user_id", "conversation_user_idx"),
    ("Message", "conversation_id", "message_conversation_idx"),
    ("Message", "role", "message_role_idx"),
    ("Meeting", "client_id", "meeting_client_idx"),
    ("Meeting", "meeting_date", "meeting_date_idx"),
    ("MeetingRoom", "client_id", "meeting_room_client_idx"),
    ("MeetingRoom", "status", "meeting_room_status_idx"),
    ("MeetingRoomMessage", "meeting_room_id", "mrm_room_idx"),
    ("MeetingRoomMessage", "agent_id", "mrm_agent_idx"),
    ("Stakeholder", "client_id", "stakeholder_client_idx"),
    ("Stakeholder", "name", "stakeholder_name_idx"),
    ("Stakeholder", "organization", "stakeholder_org_idx"),
    ("Insight", "insight_type", "insight_type_idx"),
    ("ROIOpportunity", "client_id", "roi_client_idx"),
    ("ROIOpportunity", "status", "roi_status_idx"),
    ("Agent", "name", "agent_name_idx"),
    ("Agent", "is_active", "agent_active_idx"),
    ("Concept", "category", "concept_category_idx"),
    ("Concern", "severity", "concern_severity_idx"),
    ("ActionItem", "status", "action_item_status_idx"),
]


async def initialize_schema(connection: Neo4jConnection) -> dict:
    """Initialize the Neo4j schema with constraints and indexes.

    Args:
        connection: Neo4j connection instance

    Returns:
        Dict with created constraints and indexes
    """
    results = {
        "constraints_created": [],
        "constraints_existed": [],
        "indexes_created": [],
        "indexes_existed": [],
        "errors": [],
    }

    # Create constraints
    for label, property_name, constraint_name in SCHEMA_CONSTRAINTS:
        try:
            await connection.execute_write(f"""
                CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                FOR (n:{label})
                REQUIRE n.{property_name} IS UNIQUE
            """)
            results["constraints_created"].append(constraint_name)
            logger.info(f"Created constraint: {constraint_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                results["constraints_existed"].append(constraint_name)
            else:
                results["errors"].append(f"{constraint_name}: {str(e)}")
                logger.error(f"Failed to create constraint {constraint_name}: {e}")

    # Create indexes
    for label, property_name, index_name in SCHEMA_INDEXES:
        try:
            await connection.execute_write(f"""
                CREATE INDEX {index_name} IF NOT EXISTS
                FOR (n:{label})
                ON (n.{property_name})
            """)
            results["indexes_created"].append(index_name)
            logger.info(f"Created index: {index_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                results["indexes_existed"].append(index_name)
            else:
                results["errors"].append(f"{index_name}: {str(e)}")
                logger.error(f"Failed to create index {index_name}: {e}")

    return results


async def verify_schema(connection: Neo4jConnection) -> dict:
    """Verify the current schema state.

    Returns:
        Dict with existing constraints and indexes
    """
    try:
        constraints = await connection.execute_query("SHOW CONSTRAINTS")
        indexes = await connection.execute_query("SHOW INDEXES")

        return {"constraints": constraints, "indexes": indexes, "status": "verified"}
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return {"constraints": [], "indexes": [], "status": "error", "error": str(e)}


async def clear_all_data(connection: Neo4jConnection, confirm: bool = False) -> dict:
    """Clear all nodes and relationships from the database.

    WARNING: This is destructive and should only be used in development.

    Args:
        connection: Neo4j connection instance
        confirm: Must be True to execute

    Returns:
        Dict with deletion counts
    """
    if not confirm:
        return {"error": "Must set confirm=True to clear data"}

    logger.warning("Clearing all Neo4j data!")

    try:
        # Delete all relationships first
        await connection.execute_write("MATCH ()-[r]->() DELETE r")

        # Delete all nodes
        result = await connection.execute_write("MATCH (n) DELETE n RETURN count(n) as deleted_nodes")

        deleted_count = result[0]["deleted_nodes"] if result else 0

        return {"status": "cleared", "deleted_nodes": deleted_count}
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        return {"status": "error", "error": str(e)}


# Cypher templates for common operations
CYPHER_TEMPLATES = {
    # ==========================================================================
    # Core Entity Operations
    # ==========================================================================
    # Client operations
    "upsert_client": """
        MERGE (c:Client {id: $id})
        SET c.name = $name,
            c.assistant_name = $assistant_name,
            c.updated_at = datetime()
        RETURN c
    """,
    # User operations
    "upsert_user": """
        MERGE (u:User {id: $id})
        SET u.email = $email,
            u.name = $name,
            u.role = $role,
            u.client_id = $client_id,
            u.updated_at = datetime()
        WITH u
        MATCH (c:Client {id: $client_id})
        MERGE (u)-[:BELONGS_TO]->(c)
        RETURN u
    """,
    # Agent operations
    "upsert_agent": """
        MERGE (a:Agent {id: $id})
        SET a.name = $name,
            a.display_name = $display_name,
            a.description = $description,
            a.persona = $persona,
            a.is_active = $is_active,
            a.updated_at = datetime()
        RETURN a
    """,
    # Document operations
    "upsert_document": """
        MERGE (d:Document {id: $id})
        SET d.filename = $filename,
            d.file_type = $file_type,
            d.source_platform = $source_platform,
            d.is_core_document = $is_core_document,
            d.client_id = $client_id,
            d.processing_status = $processing_status,
            d.updated_at = datetime()
        WITH d
        MATCH (c:Client {id: $client_id})
        MERGE (d)-[:OWNED_BY]->(c)
        RETURN d
    """,
    "link_document_uploader": """
        MATCH (d:Document {id: $document_id})
        MATCH (u:User {id: $user_id})
        MERGE (d)-[:UPLOADED_BY]->(u)
        RETURN d
    """,
    # Document chunk operations
    "upsert_chunk": """
        MERGE (ch:Chunk {id: $id})
        SET ch.chunk_index = $chunk_index,
            ch.content_preview = $content_preview,
            ch.updated_at = datetime()
        WITH ch
        MATCH (d:Document {id: $document_id})
        MERGE (ch)-[:PART_OF]->(d)
        RETURN ch
    """,
    # Conversation operations
    "upsert_conversation": """
        MERGE (conv:Conversation {id: $id})
        SET conv.title = $title,
            conv.client_id = $client_id,
            conv.archived = $archived,
            conv.in_knowledge_base = $in_knowledge_base,
            conv.updated_at = datetime()
        WITH conv
        MATCH (u:User {id: $user_id})
        MERGE (conv)-[:OWNED_BY]->(u)
        RETURN conv
    """,
    # Message operations
    "upsert_message": """
        MERGE (m:Message {id: $id})
        SET m.role = $role,
            m.content_preview = $content_preview,
            m.agent_id = $agent_id,
            m.updated_at = datetime()
        WITH m
        MATCH (conv:Conversation {id: $conversation_id})
        MERGE (m)-[:IN_CONVERSATION]->(conv)
        RETURN m
    """,
    "link_message_agent": """
        MATCH (m:Message {id: $message_id})
        MATCH (a:Agent {id: $agent_id})
        MERGE (a)-[:AUTHORED]->(m)
        RETURN m
    """,
    # Meeting Room operations
    "upsert_meeting_room": """
        MERGE (mr:MeetingRoom {id: $id})
        SET mr.name = $name,
            mr.description = $description,
            mr.client_id = $client_id,
            mr.status = $status,
            mr.updated_at = datetime()
        RETURN mr
    """,
    "add_meeting_room_participant": """
        MATCH (mr:MeetingRoom {id: $meeting_room_id})
        MATCH (a:Agent {id: $agent_id})
        MERGE (a)-[:PARTICIPATED_IN]->(mr)
        RETURN mr
    """,
    "upsert_meeting_room_message": """
        MERGE (mrm:MeetingRoomMessage {id: $id})
        SET mrm.content_preview = $content_preview,
            mrm.role = $role,
            mrm.discussion_round = $discussion_round,
            mrm.responding_to_agent = $responding_to_agent,
            mrm.is_autonomous = $is_autonomous,
            mrm.updated_at = datetime()
        WITH mrm
        MATCH (mr:MeetingRoom {id: $meeting_room_id})
        MERGE (mrm)-[:IN_MEETING_ROOM]->(mr)
        WITH mrm
        OPTIONAL MATCH (a:Agent {id: $agent_id})
        WHERE $agent_id IS NOT NULL
        FOREACH (_ IN CASE WHEN a IS NOT NULL THEN [1] ELSE [] END |
            MERGE (a)-[:AUTHORED]->(mrm)
        )
        RETURN mrm
    """,
    "link_meeting_room_message_response": """
        MATCH (msg:MeetingRoomMessage {id: $message_id})
        MATCH (responded_to:MeetingRoomMessage {id: $responded_to_id})
        MERGE (msg)-[r:RESPONDS_TO]->(responded_to)
        RETURN r
    """,
    # ==========================================================================
    # Stakeholder Operations
    # ==========================================================================
    "upsert_stakeholder": """
        MERGE (s:Stakeholder {id: $id})
        SET s.name = $name,
            s.role = $role,
            s.organization = $organization,
            s.client_id = $client_id,
            s.sentiment_score = $sentiment_score,
            s.total_interactions = $total_interactions,
            s.updated_at = datetime()
        RETURN s
    """,
    "create_reports_to": """
        MATCH (a:Stakeholder {id: $from_id})
        MATCH (b:Stakeholder {id: $to_id})
        MERGE (a)-[r:REPORTS_TO]->(b)
        RETURN r
    """,
    "create_influences": """
        MATCH (a:Stakeholder {id: $from_id})
        MATCH (b:Stakeholder {id: $to_id})
        MERGE (a)-[r:INFLUENCES]->(b)
        SET r.strength = $strength,
            r.influence_type = $influence_type
        RETURN r
    """,
    # ==========================================================================
    # Meeting Operations
    # ==========================================================================
    "upsert_meeting": """
        MERGE (m:Meeting {id: $id})
        SET m.title = $title,
            m.client_id = $client_id,
            m.meeting_date = date($meeting_date),
            m.meeting_type = $meeting_type,
            m.updated_at = datetime()
        RETURN m
    """,
    "create_attended": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (m:Meeting {id: $meeting_id})
        MERGE (s)-[r:ATTENDED]->(m)
        SET r.sentiment = $sentiment,
            r.speaking_time = $speaking_time
        RETURN r
    """,
    # ==========================================================================
    # Insight Operations
    # ==========================================================================
    "upsert_insight": """
        MERGE (i:Insight {id: $id})
        SET i.insight_type = $insight_type,
            i.content = $content,
            i.confidence = $confidence,
            i.sentiment = $sentiment,
            i.updated_at = datetime()
        RETURN i
    """,
    "link_stakeholder_insight": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (i:Insight {id: $insight_id})
        MERGE (s)-[r:HAS_INSIGHT]->(i)
        RETURN r
    """,
    "link_meeting_insight": """
        MATCH (m:Meeting {id: $meeting_id})
        MATCH (i:Insight {id: $insight_id})
        MERGE (m)-[r:GENERATED]->(i)
        RETURN r
    """,
    # ==========================================================================
    # ROI Operations
    # ==========================================================================
    "upsert_roi_opportunity": """
        MERGE (r:ROIOpportunity {id: $id})
        SET r.title = $title,
            r.status = $status,
            r.annual_savings = $annual_savings,
            r.client_id = $client_id,
            r.updated_at = datetime()
        RETURN r
    """,
    "create_supports": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (r:ROIOpportunity {id: $roi_id})
        MERGE (s)-[rel:SUPPORTS]->(r)
        SET rel.commitment_level = $commitment_level
        RETURN rel
    """,
    "create_blocks": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (r:ROIOpportunity {id: $roi_id})
        MERGE (s)-[rel:BLOCKS]->(r)
        SET rel.reason = $reason
        RETURN rel
    """,
    "link_meeting_roi": """
        MATCH (m:Meeting {id: $meeting_id})
        MATCH (r:ROIOpportunity {id: $roi_id})
        MERGE (m)-[rel:IDENTIFIED]->(r)
        RETURN rel
    """,
    # ==========================================================================
    # Agent Knowledge Base Operations
    # ==========================================================================
    "link_agent_knowledge": """
        MATCH (a:Agent {id: $agent_id})
        MATCH (d:Document {id: $document_id})
        MERGE (a)-[r:HAS_KNOWLEDGE_OF]->(d)
        SET r.priority = $priority,
            r.notes = $notes,
            r.updated_at = datetime()
        RETURN r
    """,
    "link_agent_expertise": """
        MERGE (e:Expertise {name: $expertise_name})
        SET e.category = $category,
            e.updated_at = datetime()
        WITH e
        MATCH (a:Agent {id: $agent_id})
        MERGE (a)-[r:EXPERT_IN]->(e)
        SET r.confidence = $confidence
        RETURN r
    """,
    "create_agent_handoff": """
        MATCH (from:Agent {id: $from_agent_id})
        MATCH (to:Agent {id: $to_agent_id})
        CREATE (from)-[r:HANDED_OFF_TO {
            conversation_id: $conversation_id,
            reason: $reason,
            timestamp: datetime($timestamp)
        }]->(to)
        RETURN r
    """,
    # ==========================================================================
    # Concept & Semantic Operations
    # ==========================================================================
    "upsert_concept": """
        MERGE (c:Concept {name: $name})
        SET c.category = $category,
            c.updated_at = datetime()
        RETURN c
    """,
    "create_discusses": """
        MATCH (m:Meeting {id: $meeting_id})
        MATCH (c:Concept {name: $concept_name})
        MERGE (m)-[r:DISCUSSES]->(c)
        SET r.frequency = coalesce(r.frequency, 0) + $frequency
        RETURN r
    """,
    "link_document_concept": """
        MATCH (d:Document {id: $document_id})
        MATCH (c:Concept {name: $concept_name})
        MERGE (d)-[r:DISCUSSES]->(c)
        SET r.frequency = coalesce(r.frequency, 0) + 1
        RETURN r
    """,
    "link_chunk_concept": """
        MATCH (ch:Chunk {id: $chunk_id})
        MERGE (c:Concept {name: $concept_name})
        ON CREATE SET c.category = $category
        MERGE (ch)-[r:MENTIONS]->(c)
        RETURN r
    """,
    "link_conversation_concept": """
        MATCH (conv:Conversation {id: $conversation_id})
        MERGE (c:Concept {name: $concept_name})
        ON CREATE SET c.category = $category
        MERGE (conv)-[r:ABOUT]->(c)
        RETURN r
    """,
    "create_concept_relationship": """
        MATCH (c1:Concept {name: $concept1})
        MATCH (c2:Concept {name: $concept2})
        MERGE (c1)-[r:RELATED_TO]->(c2)
        SET r.strength = $strength
        RETURN r
    """,
    # ==========================================================================
    # Concern & Action Item Operations
    # ==========================================================================
    "upsert_concern": """
        MERGE (c:Concern {id: $id})
        SET c.content = $content,
            c.severity = $severity,
            c.updated_at = datetime()
        RETURN c
    """,
    "link_stakeholder_concern": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (c:Concern {id: $concern_id})
        MERGE (s)-[r:RAISED]->(c)
        SET r.quote = $quote
        RETURN r
    """,
    "upsert_action_item": """
        MERGE (a:ActionItem {id: $id})
        SET a.description = $description,
            a.status = $status,
            a.due_date = $due_date,
            a.updated_at = datetime()
        RETURN a
    """,
    "link_stakeholder_action_item": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (a:ActionItem {id: $action_item_id})
        MERGE (s)-[r:ASSIGNED]->(a)
        RETURN r
    """,
    # ==========================================================================
    # Cross-Entity Reference Operations
    # ==========================================================================
    "link_message_document": """
        MATCH (m:Message {id: $message_id})
        MATCH (d:Document {id: $document_id})
        MERGE (m)-[r:REFERENCES]->(d)
        RETURN r
    """,
    "link_conversation_stakeholder": """
        MATCH (conv:Conversation {id: $conversation_id})
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MERGE (conv)-[r:MENTIONS]->(s)
        RETURN r
    """,
    "link_document_stakeholder": """
        MATCH (d:Document {id: $document_id})
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MERGE (d)-[r:ABOUT]->(s)
        RETURN r
    """,
    # ==========================================================================
    # Stakeholder-Document Relationship Operations
    # ==========================================================================
    "link_stakeholder_mentioned_in_document": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (d:Document {id: $document_id})
        MERGE (s)-[r:MENTIONED_IN]->(d)
        SET r.context = $context,
            r.mention_count = coalesce(r.mention_count, 0) + 1,
            r.updated_at = datetime()
        RETURN r
    """,
    "link_stakeholder_provided_document": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (d:Document {id: $document_id})
        MERGE (s)-[r:PROVIDED]->(d)
        SET r.date = $date,
            r.updated_at = datetime()
        RETURN r
    """,
    "link_stakeholder_concern_to_document": """
        MATCH (s:Stakeholder {id: $stakeholder_id})-[:RAISED_CONCERN]->(c:Concern)
        MATCH (d:Document {id: $document_id})
        WHERE toLower(d.filename) CONTAINS toLower(c.content)
           OR EXISTS {
               MATCH (d)-[:DISCUSSES]->(concept:Concept)
               WHERE toLower(concept.name) CONTAINS toLower(c.content)
           }
        MERGE (d)-[r:ADDRESSES]->(c)
        SET r.updated_at = datetime()
        RETURN r
    """,
    "get_stakeholder_documents": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        OPTIONAL MATCH (s)-[mentioned:MENTIONED_IN]->(d1:Document)
        OPTIONAL MATCH (s)-[provided:PROVIDED]->(d2:Document)
        OPTIONAL MATCH (d3:Document)-[about:ABOUT]->(s)
        WITH s,
             collect(DISTINCT {doc: d1, rel_type: 'MENTIONED_IN', context: mentioned.context}) as mentioned_docs,
             collect(DISTINCT {doc: d2, rel_type: 'PROVIDED', date: provided.date}) as provided_docs,
             collect(DISTINCT {doc: d3, rel_type: 'ABOUT'}) as about_docs
        RETURN s.name as stakeholder_name,
               mentioned_docs,
               provided_docs,
               about_docs
    """,
    "get_documents_mentioning_stakeholder": """
        MATCH (s:Stakeholder {id: $stakeholder_id})<-[:ABOUT|MENTIONED_IN]-(d:Document)
        RETURN d.id as id,
               d.filename as filename,
               d.file_type as file_type,
               d.source_platform as source_platform,
               d.client_id as client_id
        LIMIT $limit
    """,
    "infer_stakeholder_document_links_by_name": """
        MATCH (s:Stakeholder {client_id: $client_id})
        MATCH (d:Document {client_id: $client_id})
        WHERE d.filename CONTAINS s.name
           OR EXISTS {
               MATCH (ch:Chunk)-[:PART_OF]->(d)
               WHERE ch.content_preview CONTAINS s.name
           }
        MERGE (s)-[r:MENTIONED_IN]->(d)
        SET r.inferred = true,
            r.updated_at = datetime()
        RETURN s.name as stakeholder, d.filename as document
    """,
    "link_stakeholder_to_department_documents": """
        MATCH (s:Stakeholder {client_id: $client_id})
        WHERE s.role IS NOT NULL
        MATCH (d:Document {client_id: $client_id})
        WHERE (toLower(s.role) CONTAINS 'finance' AND toLower(d.filename) CONTAINS 'finance')
           OR (toLower(s.role) CONTAINS 'legal' AND toLower(d.filename) CONTAINS 'legal')
           OR (toLower(s.role) CONTAINS 'hr' AND toLower(d.filename) CONTAINS 'hr')
           OR (toLower(s.role) CONTAINS 'it' AND toLower(d.filename) CONTAINS 'it')
           OR (toLower(s.role) CONTAINS 'product' AND toLower(d.filename) CONTAINS 'product')
        MERGE (d)-[r:RELEVANT_TO]->(s)
        SET r.inferred_by = 'department_match',
            r.updated_at = datetime()
        RETURN s.name as stakeholder, d.filename as document
    """,
}
