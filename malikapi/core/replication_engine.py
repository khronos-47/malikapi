from datetime import datetime
import logging
from typing import List

from .checkpoint_store import CheckpointStore
from .connectors.oracle_connector import OracleConnector
from .connectors.postgres_connector import PostgresConnector

class ReplicationJob:
    def __init__(self, config, connector_config):
        """
        config: ReplicationJobConfig (pydantic)
        connector_config: dict with connection params per instance
        """
        self.config = config
        self.logger = logging.getLogger(f"Job.{config.id}")
        # connector_config example:
        # {'oracle': {'ORCL_TEST': {...}}, 'postgresql': {'pg-test': {...}}}
        self.connector_config = connector_config
        # pools/dict of connectors
        self.oracle_connectors = {}
        self.pg_connectors = {}
        # create a PG connector for checkpoint store (take first pg defined or a dedicated one)
        # For simplicity, we require a 'checkpoint_pg' entry in connector_config
        cp_pg_cfg = connector_config.get('checkpoint_pg')
        if not cp_pg_cfg:
            raise RuntimeError("connector_config must contain 'checkpoint_pg' for checkpoint store")
        self.checkpoint_pg = PostgresConnector(**cp_pg_cfg)
        self.checkpoint_store = CheckpointStore(self.checkpoint_pg)

    def _get_source_connector(self, src):
        if src.type == 'oracle':
            inst = src.instance
            if inst not in self.oracle_connectors:
                cfg = self.connector_config['oracle'][inst]
                self.oracle_connectors[inst] = OracleConnector(**cfg)
            return self.oracle_connectors[inst]
        else:
            inst = src.instance
            if inst not in self.pg_connectors:
                cfg = self.connector_config['postgresql'][inst]
                self.pg_connectors[inst] = PostgresConnector(**cfg)
            return self.pg_connectors[inst]

    def _get_target_connector(self, tgt):
        if tgt.type == 'oracle':
            inst = tgt.instance
            if inst not in self.oracle_connectors:
                cfg = self.connector_config['oracle'][inst]
                self.oracle_connectors[inst] = OracleConnector(**cfg)
            return self.oracle_connectors[inst]
        else:
            inst = tgt.instance
            if inst not in self.pg_connectors:
                cfg = self.connector_config['postgresql'][inst]
                self.pg_connectors[inst] = PostgresConnector(**cfg)
            return self.pg_connectors[inst]

    def run(self):
        self.logger.info(f"Starting job {self.config.id}")
        for rep in self.config.replications:
            try:
                self._sync_one(rep)
                self.logger.info(f"✓ Replication {rep.id} completed")
            except Exception as e:
                self.logger.exception("Replication %s failed: %s", rep.id, e)
                # record error into replication_errors table
                try:
                    cur = self.checkpoint_pg.conn.cursor()
                    cur.execute("INSERT INTO replication_errors (replication_id, error_message) VALUES (%s, %s)",
                                (rep.id, str(e)))
                    self.checkpoint_pg.conn.commit()
                    cur.close()
                except Exception:
                    pass

    def _sync_one(self, rep):
        rep_id = rep.id
        cp = self.checkpoint_store.load(rep_id)
        last_ts = cp.last_timestamp if cp else None

        # connectors
        source_conn = self._get_source_connector(rep.source)
        target_conn = self._get_target_connector(rep.target)

        # fetch delta
        rows = source_conn.fetch_delta(
            table=rep.source.table,
            columns=rep.source.columns,
            delta_column=rep.source.delta_column,
            since_timestamp=last_ts,
            schema=rep.source.schema
        )
        self.logger.info("Replication %s: fetched %d rows", rep_id, len(rows))
        if not rows:
            # update checkpoint to now to avoid refetching nothing (optional)
            self.checkpoint_store.save(rep_id, datetime.utcnow())
            return

        # optional: transform column names (we assume 1:1)
        # upsert
        target_conn.upsert_rows(
            table=rep.target.table,
            rows=rows,
            key_columns=rep.source.key_columns,
            schema=rep.target.schema
        )

        # save checkpoint as the last row's delta column
        last_row = rows[-1]
        new_ts = last_row.get(rep.source.delta_column.lower()) or last_row.get(rep.source.delta_column)
        # ensure datetime
        if isinstance(new_ts, str):
            # try parse
            from dateutil import parser
            new_ts = parser.parse(new_ts)
        if rep.source.delta_column == "UPDATED_AT":
            self.checkpoint_store.save(rep_id, new_ts)
        self.logger.info("Replication %s: checkpoint saved %s", rep_id, new_ts)
