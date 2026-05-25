```
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
```

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


markdown
# Replication Engine

Система репликации данных из Oracle в PostgreSQL с REST API, веб-интерфейсом и управлением пользователями.

## 🚀 Быстрый старт

### Предварительные требования
- Docker и Docker Compose (рекомендуемый способ)
- Или Python 3.10+ с зависимостями из `requirements.txt` (для локального запуска)
- Доступ к БД Oracle и PostgreSQL (настройки в `configs/connectors.yml`)

### Запуск через Docker (рекомендуется)

```bash
# Склонировать репозиторий
git clone <your-repo>
cd replication_engine

# Собрать и запустить все сервисы
make up

# Проверить статус
make status

# Посмотреть логи
make logs
Сервисы будут доступны:

API: http://localhost:8000

UI (Streamlit): http://localhost:8501

Управление пользователями
bash
# Создать пользователя
make cli ARGS="user create john --password secret"

# Список пользователей
make cli ARGS="user list"

# Выдать доступ к таблице
make cli ARGS="user grant-table john students"

# Забанить
make cli ARGS="user ban john --reason spam"
Генерация тестовых данных (в Oracle)
bash
# Добавить 100 студентов
make data-gen ARGS="--scenario basic --steps 100"
Остановка и очистка
bash
make down      # остановить контейнеры
make restart   # перезапустить
🛠 Локальный запуск (без Docker)
Установите зависимости:

bash
pip install -r requirements.txt
Запустите компоненты по отдельности:

bash
# Терминал 1: API
make local-api

# Терминал 2: UI
make local-ui

# Терминал 3: планировщик репликации
make local-scheduler

⚙️ Конфигурация
Подключения к БД – configs/connectors.yml

Задания репликации – configs/replication_jobs.yml

Пользователи – users.json (создаётся автоматически)

🧪 Проверка работы
Откройте UI: http://localhost:8501

Выберите таблицу в PostgreSQL или Oracle для просмотра данных

Через CLI создайте пользователя и проверьте доступ к API:

bash
curl -u john:secret http://localhost:8000/data/students?limit=5
📝 Полезные команды Make
Команда  Описание
make up  Запустить все сервисы
make down   Остановить
make logs   Логи всех сервисов
make cli ARGS="..."  Выполнить команду управления пользователями
make data-gen ARGS="..."   Сгенерировать тестовые данные
make shell  Войти в контейнер API
make local-api Запустить API локально
```