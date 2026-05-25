import random
from sqlalchemy import text
from faker_utils import fake_student

def insert_student(conn, group_id):
    s = fake_student()
    conn.execute(text("""
        INSERT INTO student (
            id, last_name, first_name, middle_name,
            passport_series, passport_number, passport_issued,
            citizenship, registration_addr, birth_date,
            group_id, updated_at
        ) VALUES (
            :id, :ln, :fn, :mn,
            :ps, :pn, :pi,
            :cit, :addr, :bd,
            :gid, CURRENT_TIMESTAMP
        )
    """), {
        "id": random.randint(100000, 999999),
        "ln": s["last_name"],
        "fn": s["first_name"],
        "mn": s["middle_name"],
        "ps": s["passport_series"],
        "pn": s["passport_number"],
        "pi": s["passport_issued"],
        "cit": s["citizenship"],
        "addr": s["registration_addr"],
        "bd": s["birth_date"],
        "gid": group_id
    })

def delete_random_student(conn):
    conn.execute(text("""
        DELETE FROM student
            WHERE id IN ( SELECT id FROM student ORDER BY DBMS_RANDOM.VALUE FETCH FIRST 1 ROWS ONLY )
    """))

def ensure_faculty(conn):
    res = conn.execute(text("SELECT id FROM faculty FETCH FIRST 1 ROWS ONLY"))
    row = res.fetchone()
    if row:
        return row[0]

    fid = random.randint(1_000, 9_999)
    conn.execute(text("""
        INSERT INTO faculty (id, name)
        VALUES (:id, :name)
    """), {"id": fid, "name": "Факультет тестовый"})
    return fid


def ensure_group(conn):
    res = conn.execute(text("SELECT id FROM student_group FETCH FIRST 1 ROWS ONLY"))
    row = res.fetchone()
    if row:
        return row[0]

    fid = ensure_faculty(conn)
    gid = random.randint(10_000, 99_999)

    conn.execute(text("""
        INSERT INTO student_group (id, name, faculty_id)
        VALUES (:id, :name, :fid)
    """), {
        "id": gid,
        "name": "Группа тестовая",
        "fid": fid
    })
    return gid