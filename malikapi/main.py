import logging
from pathlib import Path
from core.config import load_config
from core.replication_engine import ReplicationJob
import time
import yaml

# Настрой logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Задаём конфигурацию коннекторов (заполни реальные параметры)
connector_config = {
    'checkpoint_pg': {
        'host': '192.168.0.128',
        'port': 5432,
        'database': 'psqlanalytics',
        'user': 'postgres',
        'password': 'khronos'
    },
    'postgresql': {
        'pg-test': {
            'host': '192.168.0.128',
            'port': 5432,   
            'database': 'psqlanalytics',
            'user': 'postgres',
            'password': 'khronos'
        }
    },
    'oracle': {
        'ORCL_TEST': {
            'dsn': '192.168.0.128:1521/oracle_project',  # или TNS
            'user': 'replicator',
            'password': 'replicator'
        }
    }
}

def main():
    cfg = load_config('configs/replication_jobs.yml')
    # Для простоты запустим все job'ы один раз (без APScheduler)
    for job_cfg in cfg.replication_jobs:
        if not job_cfg.enabled:
            continue
        job = ReplicationJob(job_cfg, connector_config)
        job.run()

if __name__ == '__main__':
    main()
