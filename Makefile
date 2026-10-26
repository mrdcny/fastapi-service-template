.DEFAULT_GOAL := help
TEST_DATABASE_URL ?= postgresql+asyncpg://app:app@localhost:5432/app
IMAGE ?= fastapi-service-template:dev
CHART := deploy/helm/fastapi-service-template

.PHONY: help install fmt lint test test-all deps migrate run up down image helm-lint check

help: ## Show this help
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install dependencies into .venv
	uv sync

fmt: ## Format and autofix
	uv run ruff format .
	uv run ruff check --fix .

lint: ## Lint, format check and type check
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

test: ## Unit tests (no database needed)
	uv run pytest -m "not integration"

test-all: ## All tests, including integration tests against Postgres (needs `make deps`)
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) uv run pytest --cov --cov-report=term

deps: ## Start Postgres and Jaeger in Docker
	docker compose up -d --wait db jaeger

migrate: ## Apply database migrations
	uv run alembic upgrade head

run: ## Run the service locally with .env
	uv run --env-file .env python -m fastapi_service_template

up: ## Run the full stack in Docker
	docker compose up --build

down: ## Stop the stack and delete its data
	docker compose down -v

image: ## Build the production image
	docker build -t $(IMAGE) .

helm-lint: ## Lint and render the Helm chart
	helm lint --strict $(CHART) -f $(CHART)/ci/test-values.yaml
	helm template ci $(CHART) -f $(CHART)/ci/test-values.yaml > /dev/null

check: lint test-all helm-lint ## Everything CI runs, locally
