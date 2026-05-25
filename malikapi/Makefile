# ============================================
# Replication Engine - Makefile
# ============================================

.PHONY: help build up down restart logs status shell
.PHONY: api ui scheduler cli data-gen test
.PHONY: local-api local-ui local-scheduler local-cli local-data-gen

# -------------------- Docker Compose --------------------
DOCKER_COMPOSE = docker-compose
CONTAINER_API = replication-api
CONTAINER_UI = replication-ui
CONTAINER_SCHEDULER = replication-scheduler

help:
	@echo "📦 Replication Engine – доступные команды"
	@echo ""
	@echo "🐳 Docker Compose:"
	@echo "  make build         - собрать образы"
	@echo "  make up            - запустить все сервисы (api, ui, scheduler)"
	@echo "  make down          - остановить и удалить контейнеры"
	@echo "  make restart       - перезапустить все сервисы"
	@echo "  make logs          - показать логи всех сервисов (Ctrl+C для выхода)"
	@echo "  make logs-api      - логи только API"
	@echo "  make logs-ui       - логи только UI"
	@echo "  make logs-scheduler- логи только планировщика"
	@echo "  make status        - статус контейнеров"
	@echo "  make shell         - войти в bash контейнера API"
	@echo ""
	@echo "🔧 Управление пользователями (CLI):"
	@echo "  make cli ARGS='user list'   - выполнить любую команду CLI (в Docker)"
	@echo "  make local-cli ARGS='user list' - выполнить локально (без Docker)"
	@echo ""
	@echo "📊 Генерация тестовых данных:"
	@echo "  make data-gen ARGS='--steps 50' - запустить генератор (в Docker)"
	@echo "  make local-data-gen ARGS='--steps 50' - локально"
	@echo ""
	@echo "🏃 Локальный запуск (без Docker):"
	@echo "  make local-api      - запустить API через uvicorn"
	@echo "  make local-ui       - запустить Streamlit UI"
	@echo "  make local-scheduler- запустить планировщик репликации"
	@echo ""
	@echo "🧪 Тестирование:"
	@echo "  make test           - запустить тесты (если появятся)"
	@echo ""

# -------------------- Docker Compose управление --------------------
build:
	$(DOCKER_COMPOSE) build

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart

logs:
	$(DOCKER_COMPOSE) logs -f

logs-api:
	docker logs -f $(CONTAINER_API)

logs-ui:
	docker logs -f $(CONTAINER_UI)

logs-scheduler:
	docker logs -f $(CONTAINER_SCHEDULER)

status:
	$(DOCKER_COMPOSE) ps

shell:
	docker exec -it $(CONTAINER_API) bash

# -------------------- CLI (внутри Docker) --------------------
cli:
	@if docker ps --filter "name=$(CONTAINER_API)" --format "table {{.Names}}" | grep -q $(CONTAINER_API); then \
		docker exec -it $(CONTAINER_API) python malikapi/cli/app.py $(ARGS); \
	else \
		echo "⚠️  Контейнер $(CONTAINER_API) не запущен. Используйте 'make up' или 'make local-cli'"; \
		exit 1; \
	fi

# -------------------- Генератор данных (внутри Docker) --------------------
data-gen:
	@if docker ps --filter "name=$(CONTAINER_API)" --format "table {{.Names}}" | grep -q $(CONTAINER_API); then \
		docker exec -it $(CONTAINER_API) python data_generator/cli.py $(ARGS); \
	else \
		echo "⚠️  Контейнер $(CONTAINER_API) не запущен. Используйте 'make up' или 'make local-data-gen'"; \
		exit 1; \
	fi

# -------------------- Локальный запуск (без Docker) --------------------
local-api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

local-ui:
	streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0

local-scheduler:
	python scheduler_runner.py

local-cli:
	python malikapi/cli/app.py $(ARGS)

local-data-gen:
	python data_generator/cli.py $(ARGS)

# -------------------- Тесты (если будут) --------------------
test:
	pytest tests/