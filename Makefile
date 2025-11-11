TASK_ID ?=
ENV_FILE := $$(pwd)/.env.agent.local

.PHONY: sync run format lint mypy tests coverage run

hooks:
	uv run pre-commit install
	uv run pre-commit autoupdate
	uv run pre-commit install --install-hooks

sync:
	uv sync --all-extras --all-packages --group dev

format:
	uv run ruff format
	uv run ruff check --fix

lint:
	uv run ruff check

mypy:
	uv run mypy .

tests:
	uv run pytest

build:
	docker build -t agent-foundry/python312 .

coverage:
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m

app:
	otto app --env-file ${ENV_FILE}


install:
	uv pip install -e .

check:
	docker compose ps

down:
	docker compose down --remove-orphans

up: down
	docker compose --env-file .env up -d
