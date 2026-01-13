TASK_ID ?=
ENV_FILE := $(PWD)/.env
REGISTRY := registry.digitalocean.com/konnect-docker
IMAGE_NAME := otto-mcp/web
IMAGE_TAG := latest


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

coverage:
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m

app:
	otto app --env-file $(ENV_FILE) --host 0.0.0.0 --port 8000


listener:
	otto listener --env-file $(ENV_FILE)


install:
	uv pip install -e .

builder:
	docker buildx create \
		--use --name multiarch-builder \
		--driver docker-container --bootstrap

build:
	docker buildx build \
		--builder multiarch-builder \
		--platform linux/amd64,linux/arm64 \
		--tag $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) \
		--push .

check:
	docker compose ps

down:
	docker compose down --remove-orphans

up: down
	docker compose pull
	docker compose up -d

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=100

tag:
	docker tag \
		$(IMAGE_NAME) \
		$(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

push:
	docker push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

inspect:
	npx @modelcontextprotocol/inspector \
		node build/index.js
