"""
Neo4j Graph Schema Initialization

Defines and creates the graph schema including:
- Node constraints and indexes
- Relationship types
- Initial schema validation
"""

import logging
from typing import Optional

from .connection import Neo4jConnection

logger = logging.getLogger(__name__)


# Schema definition
SCHEMA_CONSTRAINTS = [
    # Unique constraints on IDs
    ("Stakeholder", "id", "stakeholder_id_unique"),
    ("Agent", "id", "agent_id_unique"),
    ("Document", "id", "document_id_unique"),
    ("Meeting", "id", "meeting_id_unique"),
    ("Insight", "id", "insight_id_unique"),
    ("ROIOpportunity", "id", "roi_opportunity_id_unique"),
    ("Concept", "name", "concept_name_unique"),
    ("Concern", "id", "concern_id_unique"),
]

SCHEMA_INDEXES = [
    # Performance indexes for common queries
    ("Stakeholder", "client_id", "stakeholder_client_idx"),
    ("Stakeholder", "name", "stakeholder_name_idx"),
    ("Stakeholder", "organization", "stakeholder_org_idx"),
    ("Document", "client_id", "document_client_idx"),
    ("Meeting", "client_id", "meeting_client_idx"),
    ("Meeting", "meeting_date", "meeting_date_idx"),
    ("Insight", "insight_type", "insight_type_idx"),
    ("ROIOpportunity", "status", "roi_status_idx"),
    ("Concept", "category", "concept_category_idx"),
]


async def initialize_schema(connection: Neo4jConnection) -> dict:
    """
    Initialize the Neo4j schema with constraints and indexes.

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
        "errors": []
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
    """
    Verify the current schema state.

    Returns:
        Dict with existing constraints and indexes
    """
    try:
        constraints = await connection.execute_query(
            "SHOW CONSTRAINTS"
        )
        indexes = await connection.execute_query(
            "SHOW INDEXES"
        )

        return {
            "constraints": constraints,
            "indexes": indexes,
            "status": "verified"
        }
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return {
            "constraints": [],
            "indexes": [],
            "status": "error",
            "error": str(e)
        }


async def clear_all_data(connection: Neo4jConnection, confirm: bool = False) -> dict:
    """
    Clear all nodes and relationships from the database.

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
        await connection.execute_write(
            "MATCH ()-[r]->() DELETE r"
        )

        # Delete all nodes
        result = await connection.execute_write(
            "MATCH (n) DELETE n RETURN count(n) as deleted_nodes"
        )

        deleted_count = result[0]["deleted_nodes"] if result else 0

        return {
            "status": "cleared",
            "deleted_nodes": deleted_count
        }
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Cypher templates for common operations
CYPHER_TEMPLATES = {
    # Stakeholder operations
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

    # Meeting operations
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

    # Insight operations
    "upsert_insight": """
        MERGE (i:Insight {id: $id})
        SET i.insight_type = $insight_type,
            i.content = $content,
            i.confidence = $confidence,
            i.updated_at = datetime()
        RETURN i
    """,

    "link_stakeholder_insight": """
        MATCH (s:Stakeholder {id: $stakeholder_id})
        MATCH (i:Insight {id: $insight_id})
        MERGE (s)-[r:HAS_INSIGHT]->(i)
        RETURN r
    """,

    # ROI operations
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

    # Concept operations
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
        SET r.frequency = $frequency
        RETURN r
    """,
}
