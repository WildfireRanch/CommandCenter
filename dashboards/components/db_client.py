"""
PostgreSQL Database Client
Direct access to CommandCenter database for analytics and monitoring
"""

import os
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

class DatabaseClient:
    """Client for direct PostgreSQL database access"""

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "")
        self.engine = None
        if self.db_url:
            try:
                self.engine = create_engine(self.db_url, pool_pre_ping=True)
            except Exception as e:
                print(f"Database connection error: {e}")

    def is_connected(self) -> bool:
        """Check if database is connected"""
        if not self.engine:
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except:
            return False

    def get_recent_energy_data(self, hours: int = 24) -> pd.DataFrame:
        """Get recent energy data from TimescaleDB"""
        if not self.engine:
            return pd.DataFrame()

        query = text("""
            SELECT
                timestamp,
                battery_soc,
                battery_voltage,
                battery_power,
                solar_power,
                load_power,
                grid_power
            FROM energy_snapshots
            WHERE timestamp >= NOW() - INTERVAL ':hours hours'
            ORDER BY timestamp DESC
            LIMIT 1000
        """)

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={"hours": hours})
            return df
        except Exception as e:
            print(f"Query error: {e}")
            return pd.DataFrame()

    def get_conversation_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages from a conversation"""
        if not self.engine:
            return []

        query = text("""
            SELECT
                role,
                content,
                created_at
            FROM conversation_messages
            WHERE session_id = :session_id
            ORDER BY created_at ASC
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {"session_id": session_id})
                return [dict(row._mapping) for row in result]
        except Exception as e:
            print(f"Query error: {e}")
            return []

    def get_recent_conversations(self, limit: int = 20) -> pd.DataFrame:
        """Get recent conversations with message counts"""
        if not self.engine:
            return pd.DataFrame()

        query = text("""
            SELECT
                c.session_id,
                c.created_at,
                c.updated_at,
                COUNT(m.id) as message_count,
                MAX(m.created_at) as last_message_at
            FROM conversations c
            LEFT JOIN conversation_messages m ON c.session_id = m.session_id
            GROUP BY c.session_id, c.created_at, c.updated_at
            ORDER BY c.updated_at DESC
            LIMIT :limit
        """)

        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={"limit": limit})
            return df
        except Exception as e:
            print(f"Query error: {e}")
            return pd.DataFrame()

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        if not self.engine:
            return {}

        try:
            with self.engine.connect() as conn:
                # Energy data count
                energy_count = conn.execute(
                    text("SELECT COUNT(*) FROM energy_snapshots")
                ).scalar()

                # Conversation count
                conv_count = conn.execute(
                    text("SELECT COUNT(*) FROM conversations")
                ).scalar()

                # Today's conversations
                today_conv = conn.execute(
                    text("""
                        SELECT COUNT(*) FROM conversations
                        WHERE created_at >= CURRENT_DATE
                    """)
                ).scalar()

                # Latest energy snapshot
                latest_energy = conn.execute(
                    text("""
                        SELECT timestamp, battery_soc, solar_power
                        FROM energy_snapshots
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """)
                ).fetchone()

                return {
                    "total_energy_snapshots": energy_count,
                    "total_conversations": conv_count,
                    "conversations_today": today_conv,
                    "latest_energy": dict(latest_energy._mapping) if latest_energy else None
                }
        except Exception as e:
            print(f"Stats error: {e}")
            return {}


# Singleton instance
db = DatabaseClient()
