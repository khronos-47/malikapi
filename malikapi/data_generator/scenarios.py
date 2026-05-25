from sqlalchemy import create_engine
from generator import insert_student, delete_random_student,ensure_group
import time

ENGINE = create_engine(
    "oracle+oracledb://replicator:replicator@192.168.0.128:1521/?service_name=oracle_project"
)

def scenario_basic(steps=100):
    with ENGINE.begin() as conn:
        for i in range(steps):
            gid = ensure_group(conn)
            insert_student(conn, group_id=gid)

            if i % 5 == 0:
                delete_random_student(conn)

