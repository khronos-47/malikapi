import time
import logging
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from core.config import load_config
from core.replication_engine import ReplicationJob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("scheduler")

def load_connector_config():
    with open("configs/connectors.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_job(job_cfg, connector_config):
    try:
        job = ReplicationJob(job_cfg, connector_config)
        job.run()
        logger.info(f"Job {job_cfg.id} completed successfully")
    except Exception as e:
        logger.exception(f"Job {job_cfg.id} failed: {e}")

def main():
    connector_config = load_connector_config()
    cfg = load_config("configs/replication_jobs.yml")
    scheduler = BackgroundScheduler()

    for job_cfg in cfg.replication_jobs:
        if not job_cfg.enabled:
            logger.info(f"Job {job_cfg.id} is disabled, skipping")
            continue
        trigger = IntervalTrigger(seconds=job_cfg.interval_seconds)
        scheduler.add_job(
            func=run_job,
            trigger=trigger,
            args=[job_cfg, connector_config],
            id=job_cfg.id,
            replace_existing=True
        )
        logger.info(f"Scheduled job {job_cfg.id} every {job_cfg.interval_seconds}s")

    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("Scheduler shut down.")

if __name__ == "__main__":
    main()