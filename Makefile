.PHONY: help preflight up down ps logs restart smoke clean migrate seed test fmt lint build

.DEFAULT_GOAL := help

BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

help:
	@echo "$(BLUE)============================================================$(NC)"
	@echo "$(BLUE)  Football Club Platform - Makefile Commands$(NC)"
	@echo "$(BLUE)============================================================$(NC)"
	@echo ""
	@echo "$(GREEN)Docker Stack:$(NC)"
	@echo "  make preflight      - Verifica porte libere"
	@echo "  make up             - Avvia stack (con preflight)"
	@echo "  make down           - Ferma stack"
	@echo "  make ps             - Stato containers"
	@echo "  make logs           - Logs stack"
	@echo "  make restart        - Restart stack"
	@echo "  make smoke          - Smoke test endpoints"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

preflight: ## Verifica porte libere prima dell'avvio
	@echo "$(BLUE)🔍 Preflight check...$(NC)"
	@pwsh ./scripts/preflight-ports.ps1 || bash ./scripts/preflight-ports.sh

up: preflight ## Start all services (con preflight)
	@echo "$(BLUE)🐳 Avvio stack Football Club Platform...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✅ Stack avviato$(NC)"
	@echo "$(YELLOW)Backend:  http://localhost:8000/docs$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3001$(NC)"
	@echo "$(YELLOW)MinIO:    http://localhost:9001 (console: 9002)$(NC)"
	@echo "$(YELLOW)Ports - DB: 5433 | Redis: 6380$(NC)"

up-prod: ## Start all services (prod profile)
	@echo "$(BLUE)Starting production services...$(NC)"
	docker compose -f infra/docker-compose.yml --profile prod up -d

build: ## Build all Docker images
	@echo "$(BLUE)🔨 Building images...$(NC)"
	docker compose build

down: ## Stop all services
	@echo "$(BLUE)🛑 Stopping services...$(NC)"
	docker compose down
	@echo "$(GREEN)✅ Stack fermato$(NC)"

ps: ## Show running containers
	@echo "$(BLUE)📊 Stato containers:$(NC)"
	docker compose ps

logs: ## Show logs for all services
	@echo "$(BLUE)📜 Logs stack (Ctrl+C per uscire):$(NC)"
	docker compose logs -f --tail=200

logs-backend: ## Show backend logs
	docker compose logs -f backend

logs-worker: ## Show worker logs
	docker compose logs -f worker

logs-frontend: ## Show frontend logs
	docker compose logs -f frontend

restart: down up ## Restart all services

smoke: ## Smoke test API endpoints
	@echo "$(BLUE)🧪 Smoke test API endpoints...$(NC)"
	@node ./scripts/smoke.js || echo "$(RED)⚠️  Smoke test fallito - vedi log$(NC)"

clean: down ## Stop services and remove volumes
	@echo "$(RED)🧹 Removing volumes...$(NC)"
	docker compose down -v
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend alembic upgrade head
	@echo "$(GREEN)Migrations complete$(NC)"

migration: ## Create a new migration (use: make migration MSG="your message")
	@echo "$(BLUE)Creating migration...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend alembic revision --autogenerate -m "$(MSG)"

downgrade: ## Rollback last migration
	@echo "$(RED)Rolling back migration...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend alembic downgrade -1

seed: ## Seed database with comprehensive demo data (idempotent)
	@echo "$(BLUE)Seeding database with demo data...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend python /app/scripts/seed_demo.py
	@echo "$(GREEN)Seed complete$(NC)"

init-migration: ## Create initial Alembic migration (if none exist)
	@echo "$(BLUE)Initializing Alembic migration...$(NC)"
	bash scripts/init_alembic_migration.sh
	@echo "$(GREEN)Migration initialization complete$(NC)"

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	bash scripts/backup_db.sh

db-restore: ## Restore database (use: make db-restore FILE=path/to/backup.sql)
	@echo "$(BLUE)Restoring database...$(NC)"
	bash scripts/restore_db.sh $(FILE)

shell-backend: ## Open shell in backend container
	docker compose -f infra/docker-compose.yml exec backend /bin/bash

shell-db: ## Open PostgreSQL shell
	docker compose -f infra/docker-compose.yml exec db psql -U app -d football_dev

shell-redis: ## Open Redis CLI
	docker compose -f infra/docker-compose.yml exec redis redis-cli

fmt: ## Format code (backend)
	@echo "$(BLUE)Formatting code...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend black app/ ml/ scripts/
	docker compose -f infra/docker-compose.yml exec backend isort app/ ml/ scripts/
	@echo "$(GREEN)Formatting complete$(NC)"

lint: ## Lint code (backend)
	@echo "$(BLUE)Linting code...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend ruff check app/ ml/ scripts/
	docker compose -f infra/docker-compose.yml exec backend mypy app/ ml/ scripts/ --ignore-missing-imports

test: ## Run backend tests
	@echo "$(BLUE)Running tests...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend pytest tests/ -v --cov=app --cov-report=html
	@echo "$(GREEN)Tests complete. Coverage: backend/htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	docker compose -f infra/docker-compose.yml exec backend pytest-watch tests/ -v

ml-train: ## Train ML models
	@echo "$(BLUE)Training ML models...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend python ml/train.py
	@echo "$(GREEN)Training complete$(NC)"

ml-health: ## Check ML model health
	@echo "$(BLUE)Checking ML health...$(NC)"
	curl -s http://localhost:8000/api/v1/ml/health | python -m json.tool

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "Backend:"
	@curl -s http://localhost:8000/healthz | python -m json.tool || echo "$(RED)Backend unhealthy$(NC)"
	@echo "\nFrontend:"
	@curl -s http://localhost:3000/api/health || echo "$(RED)Frontend unhealthy$(NC)"

verify: ## Run comprehensive diagnostics and metrics verification
	@echo "$(BLUE)Running comprehensive verification...$(NC)"
	@bash scripts/collect_diagnostics.sh
	@bash scripts/verify_metrics.sh
	@echo "$(GREEN)Verification complete. Check artifacts/ directory.$(NC)"

init: ## Initialize project (first time setup)
	@echo "$(BLUE)Initializing project...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file$(NC)"; \
	fi
	@echo "$(BLUE)Building images...$(NC)"
	docker compose -f infra/docker-compose.yml build
	@echo "$(BLUE)Starting services...$(NC)"
	docker compose -f infra/docker-compose.yml --profile dev up -d
	@echo "$(BLUE)Waiting for database...$(NC)"
	sleep 10
	@echo "$(BLUE)Initializing migrations...$(NC)"
	bash scripts/init_alembic_migration.sh || true
	@echo "$(BLUE)Running migrations...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend alembic upgrade head
	@echo "$(BLUE)Seeding database with demo data...$(NC)"
	docker compose -f infra/docker-compose.yml exec backend python /app/scripts/seed_demo.py
	@echo "$(GREEN)✓ Initialization complete!$(NC)"
	@echo "$(GREEN)Backend API: http://localhost:8000/docs$(NC)"
	@echo "$(GREEN)Frontend:    http://localhost:3000$(NC)"

reset: clean init ## Full reset (clean + init)

check-docker: ## Verify Docker Desktop setup
	@echo "$(BLUE)Checking Docker Desktop...$(NC)"
	@docker info > /dev/null 2>&1 && echo "$(GREEN)✓ Docker is running$(NC)" || (echo "$(RED)✗ Docker is not running$(NC)" && exit 1)
	@docker compose version > /dev/null 2>&1 && echo "$(GREEN)✓ Docker Compose available$(NC)" || (echo "$(RED)✗ Docker Compose not found$(NC)" && exit 1)
	@echo "$(GREEN)Docker Desktop is properly configured$(NC)"

check-resources: ## Show Docker Desktop resource usage
	@echo "$(BLUE)Docker resource usage:$(NC)"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
