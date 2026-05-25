from typing import List, Optional
from datetime import datetime
from .base import BaseConnector
import logging


import oracledb

oracledb.defaults.thin = True

class OracleConnector(BaseConnector):
    def __init__(self, dsn: str, user: str, password: str):
        self.logger = logging.getLogger("OracleConnector")
        self.conn = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        self.logger.info(f"Connected to Oracle DSN={dsn}")

    def fetch_delta(self, table: str, columns: List[str], delta_column: str,
                    since_timestamp: Optional[datetime], schema: Optional[str] = None) -> List[dict]:
        table_qual = f"{schema}.{table}" if schema else table
        cols = ", ".join(columns)
        if since_timestamp:
            sql = f"SELECT {cols} FROM {table_qual} WHERE {delta_column} > :since_ts ORDER BY {delta_column}"
            params = {'since_ts': since_timestamp}
        else:
            sql = f"SELECT {cols} FROM {table_qual} ORDER BY {delta_column}"
            params = {}
        cur = self.conn.cursor()
        cur.execute(sql, params)
        col_names = [d[0].lower() for d in cur.description]
        rows = [dict(zip(col_names, r)) for r in cur.fetchall()]
        cur.close()
        return rows

    def upsert_rows(self, table: str, rows: List[dict], key_columns: List[str], schema: Optional[str] = None) -> int:
        if not rows:
            return 0
        table_qual = f"{schema}.{table}" if schema else table
        cur = self.conn.cursor()
        # Простая стратегия: try insert, on integrity -> update
        for row in rows:
            cols = list(row.keys())
            placeholders = ", ".join([f":{i+1}" for i in range(len(cols))])
            values = [row[c] for c in cols]
            insert_sql = f"INSERT INTO {table_qual} ({', '.join(cols)}) VALUES ({placeholders})"
            try:
                cur.execute(insert_sql, values)
            except cx_Oracle.IntegrityError:
                # build update
                set_clause = ", ".join([f"{col} = :{i+1}" for i, col in enumerate(cols) if col not in key_columns])
                where_clause = " AND ".join([f"{k} = :{cols.index(k)+1}" for k in key_columns])
                update_sql = f"UPDATE {table_qual} SET {set_clause} WHERE {where_clause}"
                cur.execute(update_sql, values)
        self.conn.commit()
        cur.close()
        return len(rows)

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
