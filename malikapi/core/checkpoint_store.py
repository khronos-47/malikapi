from datetime import datetime
from typing import Optional
import logging

class Checkpoint:
    def __init__(self, replication_id: str, last_timestamp: Optional[datetime]):
        self.replication_id = replication_id
        self.last_timestamp = last_timestamp

class CheckpointStore:
    def __init__(self, pg_connector):
        self.postgres = pg_connector
        self.logger = logging.getLogger("CheckpointStore")
        # ensure table created outside or rely on migration; but try to create here
        try:
            cur = self.postgres.conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS replication_checkpoints (
                replication_id VARCHAR(255) PRIMARY KEY,
                last_timestamp TIMESTAMP WITH TIME ZONE,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """)
            self.postgres.conn.commit()
            cur.close()
        except Exception as e:
            self.logger.warning("Could not ensure checkpoint table: %s", e)

    def load(self, replication_id: str) -> Optional[Checkpoint]:
        cur = self.postgres.conn.cursor()
        cur.execute("SELECT last_timestamp FROM replication_checkpoints WHERE replication_id = %s", (replication_id,))
        row = cur.fetchone()
        cur.close()
        if row and row[0]:
            return Checkpoint(replication_id, row[0])
        return None

    def save(self, replication_id: str, last_timestamp: datetime):
        cur = self.postgres.conn.cursor()
        cur.execute("""
        INSERT INTO replication_checkpoints (replication_id, last_timestamp)
        VALUES (%s, %s)
        ON CONFLICT (replication_id) DO UPDATE SET
          last_timestamp = EXCLUDED.last_timestamp,
          updated_at = NOW()
        """, (replication_id, last_timestamp))
        self.postgres.conn.commit()
        cur.close()
