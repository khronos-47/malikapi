replication_engine/
├── core/
│   ├── replication_engine.py     # Main orchestrator
│   ├── config.py                 # Config loading & validation (Pydantic)
│   ├── checkpoint_store.py       # State persistence
│   └── connectors/
│       ├── base.py               # Base connector interface
│       ├── oracle_connector.py   # cx_Oracle wrapper
│       └── postgres_connector.py # psycopg2 wrapper
├── main.py                       # Entry point с APScheduler
├── userservice
│       ├── users.py               # Base connector interface
├── cli
│       ├── app.py               # Base connector interface
├── configs/                      # YAML конфиги
|   ├── connectors.yml            # connection config
│   └── replication_jobs.yml      # 
|── data_generator/
|   ├── generator.py              # config
│   └── cli.yml                   # точка входа 
|── ui/
|   ├── app.py                    # streamlit ui for db
└── logs/                         # Логи


## Итоговая архитектура (диаграмма)

```
┌─────────────────────────────────────────────────────────┐
│                 APScheduler (main.py)                   │
│  Manages jobs at specified intervals                    │
└──────────────┬──────────────────────────────────────────┘
               │
      ┌────────▼────────┐
      │ ReplicationJob  │ (per job_config.yml)
      │  - loads config │
      │  - orchestrates │
      └────────┬────────┘
               │
      ┌────────▼────────────────────────┐
      │  FOR each replication spec:     │
      │                                 │
      │  ┌─────────────────────────────┐│
      │  │ 1. Load Checkpoint          ││
      │  │    (last_timestamp)         ││
      │  └──────────┬──────────────────┘│
      │             │                   │
      │  ┌──────────▼──────────────────┐│
      │  │ 2. Fetch Delta              ││
      │  │    source.fetch_delta(...)  ││
      │  │    WHERE updated_at >       ││
      │  │    last_checkpoint          ││
      │  └──────────┬──────────────────┘│
      │             │                   │
      │  ┌──────────▼──────────────────┐│
      │  │ 3. Transform                ││
      │  │    Type conversions, etc    ││
      │  └──────────┬──────────────────┘│
      │             │                   │
      │  ┌──────────▼──────────────────┐│
      │  │ 4. Upsert (target)          ││
      │  │    INSERT ON CONFLICT       ││
      │  └──────────┬──────────────────┘│
      │             │                   │
      │  ┌──────────▼──────────────────┐│
      │  │ 5. Save Checkpoint          ││
      │  │    (new last_timestamp)     ││
      │  └─────────────────────────────┘│
      └─────────────────────────────────┘
               │
      ┌────────▼─────────────────────┐
      │   Data Sources & Targets     │
      │                              │
      │  ┌──────┐  ┌──────────┐      │
      │  │Oracle│──│PostgreSQL│      │
      │  └──────┘  └──────────┘      │
      │                              │
      │  (Multiple instances & DBs)  │
      └──────────────────────────────┘
               │
      ┌────────▼──────────────────────┐
      │  PostgreSQL (Central):        │
      │                               │
      │  - replication_checkpoints    │
      │  - replication_errors         │
      │  (metadata store)             │
      └───────────────────────────────┘
```