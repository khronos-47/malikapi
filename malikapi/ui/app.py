import streamlit as st
import yaml
import pandas as pd
from sqlalchemy import create_engine, text

# ======================
# Загрузка конфигов
# ======================
@st.cache_resource
def load_connectors():
    with open("configs/connectors.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

connectors = load_connectors()

# ======================
# Создание SQLAlchemy engine
def kal():
    pass
# ======================
@st.cache_resource
def pg_engine(instance):
    cfg = connectors["postgresql"][instance]
    url = (
        f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )
    return create_engine(url)

@st.cache_resource
def oracle_engine(instance):
    cfg = connectors["oracle"][instance]

    url = (
        f"oracle+oracledb://{cfg['user']}:{cfg['password']}"
        f"@{cfg['dsn']}"
    )

    return create_engine(
        url,
        pool_pre_ping=True
    )

# ======================
# UI
# ======================
st.set_page_config(page_title="Replication Monitor", layout="wide")
st.title("🔁 Replication Monitor")

tab_pg, tab_oracle, tab_cp, tab_err, tab_diff = st.tabs(
    ["PostgreSQL", "Oracle", "Checkpoints", "Errors", "Diff"]
)

# ======================
# PostgreSQL viewer
# ======================
with tab_pg:
    st.header("📦 PostgreSQL")

    pg_inst = st.selectbox("Postgres instance", list(connectors["postgresql"].keys()))
    schema = st.text_input("Schema", "public")

    eng = pg_engine(pg_inst)

    tables = pd.read_sql(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        """,
        eng,
        params=(schema,)
    )

    table = st.selectbox("Table", tables["table_name"].tolist())

    if st.button("Load data", key = "loh"):
        df = pd.read_sql(
            f'SELECT * FROM "{schema}"."{table}" ',
            eng
        )
        st.dataframe(df, use_container_width=True)


# ======================
# Oracle viewer
# ======================
with tab_oracle:
    st.header("🏛 Oracle")

    ora_inst = st.selectbox("Oracle instance", list(connectors["oracle"].keys()))
    schema = st.text_input("Schema", "REPLICATOR")

    eng = oracle_engine(ora_inst)

    tables = pd.read_sql(
        """
        SELECT table_name
        FROM all_tables
        WHERE owner = :schema
        ORDER BY table_name
        """,
        eng,
        params={"schema": schema.upper()}
    )
    
    # Нормализуем имена колонок
    tables.columns = tables.columns.str.upper()  # или .str.lower()
    
    # Проверяем, что нужная колонка существует
    if 'TABLE_NAME' not in tables.columns and len(tables.columns) > 0:
        # Берем первую колонку, какую бы имя она ни имела
        tables = tables.rename(columns={tables.columns[0]: 'TABLE_NAME'})
    
    table = st.selectbox("Table", tables["TABLE_NAME"].tolist())

    if st.button("Load data", key = "loh1"):
        df = pd.read_sql(
            f'SELECT * FROM {schema}.{table}',
            eng
        )
        st.dataframe(df, use_container_width=True)

# ======================
# Checkpoints
# ======================



