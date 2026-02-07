"""
Database module for Wisp call persistence
Handles SQLite database operations for storing call data
"""
import aiosqlite
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = "wisp_calls.db"


async def init_database():
    """Initialize database and create tables if they don't exist"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS calls (
                    call_id TEXT PRIMARY KEY,
                    from_number TEXT,
                    to_number TEXT,
                    started_at TEXT,
                    status TEXT,
                    screening_verdict TEXT,
                    screening_summary TEXT,
                    screened_at TEXT,
                    transcript TEXT,
                    terminated_at TEXT,
                    transfer_initiated INTEGER DEFAULT 0,
                    transfer_target TEXT,
                    transfer_initiated_at TEXT,
                    transferred_to TEXT,
                    transferred_at TEXT,
                    ended_at TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            await db.commit()
            logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


@asynccontextmanager
async def get_db_connection():
    """Get async database connection context manager"""
    async with aiosqlite.connect(DB_PATH) as db:
        yield db


async def create_or_update_call(call_data: Dict[str, Any]) -> bool:
    """
    Create or update a call record in the database.
    Uses INSERT OR REPLACE to handle both new and existing calls.
    
    Args:
        call_data: Dictionary containing call information
        
    Returns:
        True if successful, False otherwise
    """
    try:
        now = datetime.utcnow().isoformat()
        
        # Ensure created_at and updated_at are set
        if "created_at" not in call_data:
            # Check if call exists to preserve original created_at
            existing = await get_call(call_data.get("call_id"))
            if existing:
                call_data["created_at"] = existing.get("created_at", now)
            else:
                call_data["created_at"] = now
        
        call_data["updated_at"] = now
        
        async with get_db_connection() as db:
            await db.execute("""
                INSERT OR REPLACE INTO calls (
                    call_id, from_number, to_number, started_at, status,
                    screening_verdict, screening_summary, screened_at, transcript,
                    terminated_at, transfer_initiated, transfer_target, transfer_initiated_at,
                    transferred_to, transferred_at, ended_at, created_at, updated_at
                ) VALUES (
                    :call_id, :from_number, :to_number, :started_at, :status,
                    :screening_verdict, :screening_summary, :screened_at, :transcript,
                    :terminated_at, :transfer_initiated, :transfer_target, :transfer_initiated_at,
                    :transferred_to, :transferred_at, :ended_at, :created_at, :updated_at
                )
            """, {
                "call_id": call_data.get("call_id"),
                "from_number": call_data.get("from_number"),
                "to_number": call_data.get("to_number"),
                "started_at": call_data.get("started_at"),
                "status": call_data.get("status"),
                "screening_verdict": call_data.get("screening_verdict"),
                "screening_summary": call_data.get("screening_summary"),
                "screened_at": call_data.get("screened_at"),
                "transcript": call_data.get("transcript"),
                "terminated_at": call_data.get("terminated_at"),
                "transfer_initiated": 1 if call_data.get("transfer_initiated") else 0,
                "transfer_target": call_data.get("transfer_target"),
                "transfer_initiated_at": call_data.get("transfer_initiated_at"),
                "transferred_to": call_data.get("transferred_to"),
                "transferred_at": call_data.get("transferred_at"),
                "ended_at": call_data.get("ended_at"),
                "created_at": call_data.get("created_at"),
                "updated_at": call_data.get("updated_at")
            })
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error creating/updating call in database: {e}", exc_info=True)
        return False


async def get_call(call_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a call record by call_id.
    
    Args:
        call_id: Unique call identifier
        
    Returns:
        Dictionary containing call data, or None if not found
    """
    try:
        async with get_db_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM calls WHERE call_id = ?",
                (call_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    except Exception as e:
        logger.error(f"Error retrieving call from database: {e}", exc_info=True)
        return None


async def get_all_calls(limit: Optional[int] = None) -> list[Dict[str, Any]]:
    """
    Retrieve all calls from the database.
    
    Args:
        limit: Optional limit on number of calls to return
        
    Returns:
        List of dictionaries containing call data
    """
    try:
        async with get_db_connection() as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM calls ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error retrieving all calls from database: {e}", exc_info=True)
        return []
