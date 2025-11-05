# ============================================================================
# Football Club Platform - Makefile
# Professional Development & Deployment Commands
# ============================================================================

.PHONY: help
help: ## Show this help message
	@echo "Football Club Platform - Available Commands"
	@echo "==========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# DOCKER COMMANDS
# ============================================================================

.PHONY: up
up: ## Start all services
	docker-compose up -d

.PHONY: down
down: ## Stop all services
	docker-compose down

.PHONY: restart
restart: down up ## Restart all services

.PHONY: logs
logs: ## View logs (use SERVICE=name for specific service)
	docker-compose logs -f $(SERVICE)

.PHONY: ps
ps: ## List running containers
	docker-compose ps

.PHONY: build
build: ## Build all images
	docker-compose build

# ============================================================================
# DATABASE COMMANDS
# ============================================================================

.PHONY: db-shell
db-shell: ## Open PostgreSQL shell
	docker exec -it football_club_platform_db psql -U app -d football_club_platform

.PHONY: migrate
migrate: ## Run Alembic migrations
	docker exec football_club_platform_backend alembic upgrade head

.PHONY: migrate-down
migrate-down: ## Rollback one migration
	docker exec football_club_platform_backend alembic downgrade -1

.PHONY: migrate-reset
migrate-reset: ## Reset all migrations (WARNING: DESTRUCTIVE)
	docker exec football_club_platform_backend alembic downgrade base

.PHONY: migration-create
migration-create: ## Create new migration (use MSG="description")
	docker exec football_club_platform_backend alembic revision --autogenerate -m "$(MSG)"

# ============================================================================
# SEEDING COMMANDS
# ============================================================================

.PHONY: seed
seed: ## Seed database (DATASET=minimal|staging|demo, default: minimal)
	@echo "🌱 Seeding database with dataset: $(or $(DATASET),minimal)"
	DATASET=$(or $(DATASET),minimal) docker exec football_club_platform_backend python -m seeds.runner

.PHONY: seed-minimal
seed-minimal: ## Seed with minimal dataset (CI/testing)
	@$(MAKE) seed DATASET=minimal

.PHONY: seed-staging
seed-staging: ## Seed with staging dataset
	@$(MAKE) seed DATASET=staging

.PHONY: seed-demo
seed-demo: ## Seed with demo dataset (rich data)
	@$(MAKE) seed DATASET=demo

.PHONY: reseed
reseed: migrate-reset migrate seed ## Full reseed: reset migrations + migrate + seed
	@echo "✅ Database fully reseeded"

.PHONY: reseed-minimal
reseed-minimal: ## Reseed with minimal dataset
	@$(MAKE) reseed DATASET=minimal

.PHONY: reseed-demo
reseed-demo: ## Reseed with demo dataset
	@$(MAKE) reseed DATASET=demo

# ============================================================================
# TESTING COMMANDS
# ============================================================================

.PHONY: test
test: ## Run tests
	docker exec football_club_platform_backend pytest

.PHONY: test-seeds
test-seeds: ## Run seed tests
	docker exec football_club_platform_backend pytest tests/test_seeds.py -v

.PHONY: test-cov
test-cov: ## Run tests with coverage
	docker exec football_club_platform_backend pytest --cov=app --cov-report=html

# ============================================================================
# CODE QUALITY COMMANDS
# ============================================================================

.PHONY: lint
lint: ## Run linters
	docker exec football_club_platform_backend ruff check app

.PHONY: format
format: ## Format code
	docker exec football_club_platform_backend ruff format app

.PHONY: type-check
type-check: ## Run type checking
	docker exec football_club_platform_backend mypy app

# ============================================================================
# UTILITY COMMANDS
# ============================================================================

.PHONY: shell
shell: ## Open backend shell
	docker exec -it football_club_platform_backend bash

.PHONY: clean
clean: ## Clean temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

.PHONY: prune
prune: ## Prune Docker system (WARNING: removes unused data)
	docker system prune -af --volumes

# ============================================================================
# PORT VALIDATION
# ============================================================================

.PHONY: check-ports
check-ports: ## Verify port configuration (ensures no conflict with pythonpro)
	@echo "Checking port configuration..."
	@if [ "$(FCP_WEB_PORT)" = "3001" ]; then \
		echo "❌ ERROR: FCP_WEB_PORT=3001 is RESERVED for pythonpro!"; \
		exit 1; \
	fi
	@echo "✅ Port configuration OK"
	@echo "   FCP_WEB_PORT: $(or $(FCP_WEB_PORT),3000)"
	@echo "   FCP_API_PORT: $(or $(FCP_API_PORT),8000)"
	@echo "   FCP_DB_PORT: $(or $(FCP_DB_PORT),5434)"
	@echo "   FCP_REDIS_PORT: $(or $(FCP_REDIS_PORT),6381)"

# ============================================================================
# QUICKSTART
# ============================================================================

.PHONY: quickstart
quickstart: check-ports up migrate seed-minimal ## Quickstart: up + migrate + seed minimal
	@echo "🎉 Football Club Platform is ready!"
	@echo "   Frontend: http://localhost:$(or $(FCP_WEB_PORT),3000)"
	@echo "   Backend API: http://localhost:$(or $(FCP_API_PORT),8000)"
	@echo "   API Docs: http://localhost:$(or $(FCP_API_PORT),8000)/docs"

# ============================================================================
# WINDOWS-SPECIFIC COMMANDS (PowerShell)
# ============================================================================

.PHONY: quickstart-win
quickstart-win: ## Quickstart for Windows
	@powershell -Command "docker-compose up -d"
	@powershell -Command "Start-Sleep -Seconds 10"
	@powershell -Command "docker exec football_club_platform_backend alembic upgrade head"
	@powershell -Command "docker exec football_club_platform_backend python -m seeds.runner"
	@echo "🎉 Football Club Platform is ready on Windows!"
