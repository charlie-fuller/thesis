"""
Neo4j Connection Management

Provides async-compatible connection handling for Neo4j Aura.
Uses the official neo4j Python driver with connection pooling.
"""

import logging
import os
from typing import Any, Optional
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)

# Global connection instance
_neo4j_connection: Optional["Neo4jConnection"] = None


class Neo4jConnection:
    """
    Manages Neo4j database connections with async support.

    Uses connection pooling and provides both query execution
    and transaction support.
    """

    def __init__(
        self,
        uri: str,
        password: str,
        username: str = "neo4j",
        database: str = "neo4j",
        max_connection_pool_size: int = 50
    ):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI (e.g., neo4j+s://xxx.databases.neo4j.io)
            password: Database password
            username: Database username (default: neo4j)
            database: Database name (default: neo4j)
            max_connection_pool_size: Maximum connections in pool
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver: Optional[AsyncDriver] = None
        self._max_pool_size = max_connection_pool_size

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        if self._driver is not None:
            return

        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_pool_size=self._max_pool_size
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    async def execute_query(
        self,
        cypher: str,
        params: Optional[dict] = None,
        database: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            cypher: Cypher query string
            params: Query parameters
            database: Database name (uses default if not specified)

        Returns:
            List of result records as dictionaries
        """
        if self._driver is None:
            await self.connect()

        db = database or self.database
        params = params or {}

        try:
            async with self._driver.session(database=db) as session:
                result = await session.run(cypher, params)
                records = await result.data()
                return records
        except Exception as e:
            logger.error(f"Query execution failed: {e}\nQuery: {cypher}")
            raise

    async def execute_write(
        self,
        cypher: str,
        params: Optional[dict] = None,
        database: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a write transaction (CREATE, MERGE, DELETE, etc.).

        Args:
            cypher: Cypher query string
            params: Query parameters
            database: Database name (uses default if not specified)

        Returns:
            List of result records as dictionaries
        """
        if self._driver is None:
            await self.connect()

        db = database or self.database
        params = params or {}

        async def _write_tx(tx):
            result = await tx.run(cypher, params)
            return await result.data()

        try:
            async with self._driver.session(database=db) as session:
                records = await session.execute_write(_write_tx)
                return records
        except Exception as e:
            logger.error(f"Write transaction failed: {e}\nQuery: {cypher}")
            raise

    @asynccontextmanager
    async def session(self, database: Optional[str] = None):
        """
        Get a Neo4j session for multiple operations.

        Usage:
            async with connection.session() as session:
                await session.run("MATCH (n) RETURN n")
        """
        if self._driver is None:
            await self.connect()

        db = database or self.database
        session = self._driver.session(database=db)
        try:
            yield session
        finally:
            await session.close()

    async def health_check(self) -> dict[str, Any]:
        """
        Check Neo4j connection health.

        Returns:
            Dict with status, version, and database info
        """
        try:
            if self._driver is None:
                await self.connect()

            # Get server info
            result = await self.execute_query(
                "CALL dbms.components() YIELD name, versions RETURN name, versions"
            )

            return {
                "status": "healthy",
                "uri": self.uri,
                "database": self.database,
                "components": result
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "uri": self.uri,
                "database": self.database
            }


async def get_neo4j_connection() -> Neo4jConnection:
    """
    Get or create the global Neo4j connection.

    Uses environment variables:
        NEO4J_URI: Connection URI
        NEO4J_PASSWORD: Database password
        NEO4J_USERNAME: Database username (default: neo4j)
        NEO4J_DATABASE: Database name (default: neo4j)

    Returns:
        Neo4jConnection instance
    """
    global _neo4j_connection

    if _neo4j_connection is None:
        uri = os.getenv("NEO4J_URI")
        password = os.getenv("NEO4J_PASSWORD")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not uri or not password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD environment variables are required")

        _neo4j_connection = Neo4jConnection(
            uri=uri,
            password=password,
            username=username,
            database=database
        )
        await _neo4j_connection.connect()

    return _neo4j_connection


async def close_neo4j_connection() -> None:
    """Close the global Neo4j connection."""
    global _neo4j_connection

    if _neo4j_connection is not None:
        await _neo4j_connection.close()
        _neo4j_connection = None
