# api/main.py
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional

import yaml
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import create_engine
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import uvicorn

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from userservice.users import Users
from userservice.reader import SimpleUserStorage

# -------------------- Конфигурация --------------------
# Загрузка коннекторов

def load_connectors():
    #config_path = Path(__file__).parent.parent / "configs" / "connectors.yml"
    with open("configs/connectors.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

connectors = load_connectors()
TARGET_INSTANCE = "pg-test"
TARGET_SCHEMA = "public"

# -------------------- Rate Limiting --------------------
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Replication Data API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Кастомный ключ для лимита – по имени пользователя (после аутентификации)
def get_user_key(request: Request, user: Users = Depends(...)) -> str:
    # Этот декоратор будет использоваться после аутентификации
    return f"user:{user.username}"

# -------------------- Аутентификация --------------------
security = HTTPBasic()

def get_pg_engine():
    cfg = connectors["postgresql"][TARGET_INSTANCE]
    url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    return create_engine(url)

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = Users(credentials.username, password=credentials.password, create_if_missing=False)
    if not user.check_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.user.get('status', {}).get('banned'):
        reason = user.user.get('status', {}).get('banned').get("reason")
        raise HTTPException(status_code=403, detail=f"User is banned reason: {reason} ")
    return user

def check_table_permission(user: Users, table: str, requested_columns: List[str] = None):
    tables = user.user.get('tables', {})
    if table not in tables:
        raise HTTPException(status_code=403, detail=f"No access to table {table}")
    allowed_cols = tables[table].get('columns', [])
    if allowed_cols == []:
        if requested_columns is None:
            return None
        return requested_columns
    else:
        if requested_columns is None:
            return allowed_cols
        for col in requested_columns:
            if col not in allowed_cols:
                raise HTTPException(status_code=403, detail=f"Column {col} not allowed")
        return requested_columns

# -------------------- Эндпоинты --------------------
@app.get("/data/{table}")
@limiter.limit("60/minute")  # 60 запросов в минуту
async def get_table_data(
    request: Request,
    table: str,
    columns: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: Users = Depends(get_current_user)
):
    req_cols = columns.split(',') if columns else None
    allowed_columns = check_table_permission(user, table, req_cols)
    engine = get_pg_engine()
    col_str = "*" if allowed_columns is None else ", ".join(f'"{c}"' for c in allowed_columns)
    query = f'SELECT {col_str} FROM "{TARGET_SCHEMA}"."{table}" LIMIT %(limit)s OFFSET %(offset)s'
    try:
        df = pd.read_sql(query, engine, params={"limit": limit, "offset": offset})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    user.add_request({
        "endpoint": f"/data/{table}",
        "query": query,
        "params": {"columns": columns, "limit": limit, "offset": offset},
        "result_rows": len(df)
    })
    return df.to_dict(orient="records")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/query")
@limiter.limit("30/minute")
async def execute_sql(request: Request, sql: str, user: Users = Depends(get_current_user)):
    if user.username != "admin":
        raise HTTPException(status_code=403, detail="Only admin can execute raw SQL")
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    engine = get_pg_engine()
    try:
        df = pd.read_sql(sql, engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    user.add_request({
        "endpoint": "/query",
        "query": sql,
        "result_rows": len(df)
    })
    return df.to_dict(orient="records")

# -------------------- Метаданные пользователя --------------------
@app.get("/my/profile")
async def get_my_profile(user: Users = Depends(get_current_user)):
    """Возвращает информацию о пользователе (без пароля и uuid, если не нужно)"""
    profile = {
        "username": user.username,
        "status": user.user.get("status", {}).get("user_status"),
        "banned": bool(user.user.get("status", {}).get("banned")),
        "created_at": user.user.get("created_at"),
        "updated_at": user.user.get("updated_at"),
    }
    return profile

@app.get("/my/tables")
async def get_my_tables(user: Users = Depends(get_current_user)):
    """Возвращает список таблиц с разрешёнными колонками"""
    tables = user.user.get("tables", {})
    result = []
    for table_name, info in tables.items():
        result.append({
            "table": table_name,
            "allowed_columns": info.get("columns", [])  # [] означает все колонки
        })
    return {"tables": result}

# -------------------- Фоновая очистка users.json --------------------
def cleanup_users_requests():
    """Удаляет старые записи requests у всех пользователей (оставляет последние 1000)"""
    storage = SimpleUserStorage()
    all_users = storage.get_all_users()
    modified = False
    for username, data in all_users.items():
        requests = data.get("requests", [])
        if len(requests) > 1000:
            # оставляем последние 1000
            data["requests"] = requests[-1000:]
            modified = True
        # также можно удалить записи старше 30 дней (опционально)
        # но для простоты оставим ограничение по количеству
    if modified:
        # сохраняем всех обратно (нужен метод save_all_users)
        # В SimpleUserStorage добавим метод save_all_users
        storage.save_all_users(all_users)

# Запускаем фоновый планировщик
scheduler = BackgroundScheduler()
scheduler.add_job(
    cleanup_users_requests,
    trigger=IntervalTrigger(hours=24),  # раз в сутки
    id="cleanup_requests",
    replace_existing=True
)
scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

# -------------------- Запуск --------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)