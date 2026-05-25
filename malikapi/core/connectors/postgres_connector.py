import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Optional
from datetime import datetime
from .base import BaseConnector
import logging

class PostgresConnector(BaseConnector):
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.logger = logging.getLogger("PostgresConnector")
        self.conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
        self.logger.info(f"Connected to Postgres {host}:{port}/{database}")

    def fetch_delta(self, table: str, columns: List[str], delta_column: str,
                    since_timestamp: Optional[datetime], schema: Optional[str] = None) -> List[dict]:
        schema = schema or 'public'
        table_qual = f"{schema}.{table}"
        cols = ", ".join(columns)
        if since_timestamp:
            sql = f"SELECT {cols} FROM {table_qual} WHERE {delta_column} > %s ORDER BY {delta_column}"
            params = (since_timestamp,)
        else:
            sql = f"SELECT {cols} FROM {table_qual} ORDER BY {delta_column}"
            params = ()
        cur = self.conn.cursor()
        cur.execute(sql, params)
        col_names = [d[0] for d in cur.description]
        rows = [dict(zip(col_names, r)) for r in cur.fetchall()]
        cur.close()
        return rows

    def upsert_rows(self, table: str, rows: List[dict], key_columns: List[str], schema: Optional[str] = None) -> int:
        if not rows:
            return 0
        schema = schema or 'public'
        table_qual = f"{schema}.{table}"
        cols = list(rows[0].keys())
        conflict_cols = ", ".join(key_columns)
        set_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols if c not in key_columns])
        sql = f"INSERT INTO {table_qual} ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))}) ON CONFLICT ({conflict_cols}) DO UPDATE SET {set_clause}"
        values_list = [tuple(row[c] for c in cols) for row in rows]
        cur = self.conn.cursor()
        execute_batch(cur, sql, values_list, page_size=1000)
        self.conn.commit()
        cur.close()
        return len(rows)

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
