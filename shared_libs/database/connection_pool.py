"""
Database Connection Pool for HolisticOS MVP
Implements a singleton connection pool manager optimized for Render 0.5 CPU instances
"""

import asyncio
import asyncpg
import logging
import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime

# Import our custom exceptions
from shared_libs.exceptions.holisticos_exceptions import (
    DatabaseException, 
    ConfigurationException,
    RetryableException
)

logger = logging.getLogger(__name__)

class DatabasePool:
    """
    Singleton connection pool manager for PostgreSQL connections
    Optimized for 0.5 CPU Render instances with proper resource management
    """
    
    _instance = None
    _pool = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self, database_url: str = None):
        """
        Initialize the connection pool with configuration optimized for 0.5 CPU
        Uses Supabase connection details from environment variables
        
        Args:
            database_url: PostgreSQL connection URL (defaults to constructed from Supabase vars)
        """
        if self._initialized and self._pool is not None:
            logger.debug("Database pool already initialized")
            return
        
        # Build database URL from Supabase environment variables if not provided
        if not database_url:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY") 
            database_url = os.getenv("DATABASE_URL")
            
            # If DATABASE_URL is not set, construct from Supabase URL
            if not database_url and supabase_url:
                # Extract database connection from Supabase URL
                # Supabase URL format: https://[project-id].supabase.co
                if "supabase.co" in supabase_url:
                    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
                    # Construct PostgreSQL connection URL for Supabase
                    database_url = f"postgresql://postgres.{project_id}:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
                    logger.debug(f"Constructed database URL from Supabase URL for project: {project_id}")
                    
        if not database_url:
            raise ConfigurationException(
                "DATABASE_URL not found. Please set DATABASE_URL or SUPABASE_URL environment variables"
            )
        
        # Pool configuration optimized for 0.5 CPU Render instance
        pool_config = {
            "dsn": database_url,
            "min_size": int(os.getenv("DATABASE_POOL_MIN_SIZE", "2")),     # Minimum connections (always ready)
            "max_size": int(os.getenv("DATABASE_POOL_MAX_SIZE", "8")),     # Maximum connections (safe for 0.5 CPU)
            "max_queries": int(os.getenv("DATABASE_MAX_QUERIES", "1000")), # Recycle connection after 1000 queries
            "max_inactive_connection_lifetime": int(os.getenv("DATABASE_MAX_IDLE_TIME", "300")),  # 5 minutes idle timeout
            "command_timeout": int(os.getenv("DATABASE_COMMAND_TIMEOUT", "30")),  # 30 second query timeout
            "server_settings": {
                "application_name": "holisticos_mvp",
                "timezone": "UTC"
            }
        }
        
        try:
            logger.debug(f"Initializing database pool with config: min={pool_config['min_size']}, max={pool_config['max_size']}")
            self._pool = await asyncpg.create_pool(**pool_config)
            self._initialized = True
            
            # Test the pool with a simple query
            await self._health_check()
            
            logger.debug(f"✅ Database pool initialized successfully: {pool_config['min_size']}-{pool_config['max_size']} connections")
            
        except asyncpg.PostgresError as e:
            logger.error(f"PostgreSQL error during pool initialization: {e}")
            raise DatabaseException(f"Failed to create database pool: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during pool initialization: {e}")
            raise DatabaseException(f"Failed to create database pool: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get a connection from the pool using context manager pattern
        Ensures proper connection cleanup and error handling
        """
        if not self._initialized or self._pool is None:
            await self.initialize()
        
        connection = None
        try:
            # Acquire connection with timeout
            connection = await asyncio.wait_for(
                self._pool.acquire(), 
                timeout=5.0  # 5 second timeout to get connection
            )
            yield connection
            
        except asyncio.TimeoutError:
            logger.error("Timeout acquiring database connection from pool")
            raise DatabaseException("Database connection pool exhausted - timeout acquiring connection")
        except asyncpg.PostgresError as e:
            logger.error(f"PostgreSQL error: {e}")
            raise DatabaseException(f"Database connection error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error acquiring connection: {e}")
            raise DatabaseException(f"Failed to acquire database connection: {e}")
        finally:
            if connection:
                try:
                    await self._pool.release(connection)
                except Exception as e:
                    logger.error(f"Error releasing connection back to pool: {e}")
    
    async def execute_query(self, query: str, *args) -> list:
        """
        Execute a SELECT query using a pooled connection
        
        Args:
            query: SQL SELECT query
            *args: Query parameters
            
        Returns:
            List of Record objects
        """
        async with self.get_connection() as conn:
            try:
                return await conn.fetch(query, *args)
            except asyncpg.PostgresError as e:
                logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
                raise DatabaseException(f"Database query failed: {e}")
    
    async def execute_one(self, query: str, *args):
        """
        Execute a query and return one result
        
        Args:
            query: SQL query
            *args: Query parameters
            
        Returns:
            Single Record object or None
        """
        async with self.get_connection() as conn:
            try:
                return await conn.fetchrow(query, *args)
            except asyncpg.PostgresError as e:
                logger.error(f"Fetchrow execution failed: {query[:100]}... Error: {e}")
                raise DatabaseException(f"Database fetchrow failed: {e}")
    
    async def execute_command(self, command: str, *args) -> str:
        """
        Execute a command (INSERT/UPDATE/DELETE)
        
        Args:
            command: SQL command
            *args: Command parameters
            
        Returns:
            Command status string
        """
        async with self.get_connection() as conn:
            try:
                return await conn.execute(command, *args)
            except asyncpg.PostgresError as e:
                logger.error(f"Command execution failed: {command[:100]}... Error: {e}")
                raise DatabaseException(f"Database command failed: {e}")
    
    async def execute_transaction(self, operations: list):
        """
        Execute multiple operations in a transaction
        
        Args:
            operations: List of (query, args) tuples
            
        Returns:
            List of results
        """
        async with self.get_connection() as conn:
            try:
                async with conn.transaction():
                    results = []
                    for query, args in operations:
                        if query.strip().upper().startswith('SELECT'):
                            result = await conn.fetch(query, *args)
                        else:
                            result = await conn.execute(query, *args)
                        results.append(result)
                    return results
            except asyncpg.PostgresError as e:
                logger.error(f"Transaction failed: {e}")
                raise DatabaseException(f"Database transaction failed: {e}")
    
    async def close(self):
        """Close the connection pool"""
        if self._pool:
            try:
                await self._pool.close()
                self._pool = None
                self._initialized = False
                logger.debug("✅ Database pool closed successfully")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
                raise DatabaseException(f"Failed to close database pool: {e}")
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """
        Get pool statistics for monitoring
        
        Returns:
            Dictionary with pool status and metrics
        """
        if not self._initialized or not self._pool:
            return {
                "status": "not_initialized",
                "initialized": False,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            return {
                "status": "healthy",
                "initialized": True,
                "current_size": self._pool.get_size(),
                "idle_connections": self._pool.get_idle_size(),
                "max_size": self._pool.get_max_size(),
                "min_size": self._pool.get_min_size(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {
                "status": "error",
                "initialized": self._initialized,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _health_check(self):
        """Internal health check to verify pool functionality"""
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    raise DatabaseException("Health check failed - unexpected result")
            logger.debug("Database pool health check passed")
        except Exception as e:
            logger.error(f"Database pool health check failed: {e}")
            raise DatabaseException(f"Database pool health check failed: {e}")

# Global pool instance - singleton pattern
db_pool = DatabasePool()

# Convenience functions for backward compatibility
async def get_database_connection():
    """Get a database connection from the global pool"""
    return db_pool.get_connection()

async def initialize_database_pool(database_url: str = None):
    """Initialize the global database pool"""
    return await db_pool.initialize(database_url)

async def close_database_pool():
    """Close the global database pool"""
    return await db_pool.close()

async def get_database_pool_status():
    """Get the status of the global database pool"""
    return await db_pool.get_pool_status()