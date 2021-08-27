dev-api:
    docker compose --profile testing up -d

dev-api-standalone:
    docker compose -f docker-compose.yml up -d

dev-api-local:
    docker compose --profile testing up -d db test-db
    uvicorn main:app --app-dir app/ --reload --port 8000 --host 0.0.0.0

lint:
	flake8 app/invoice app/routes app/test app/utils --max-line-length=120

lint-format:
	black app/invoice app/routes app/test app/utils --line-length=120
	autoflake app/invoice app/routes app/test app/utils --remove-unused-variables --remove-all-unused-imports --in-place -r
	isort app/invoice app/routes app/test app/utils

test:
    docker compose --profile testing up -d
    docker compose exec -T pytest --workers auto

test-local:
    docker compose --profile testing up -d test-db
    cd app && python -m pytest --workers auto

test_db:
	docker up arboreum_backend

create_db:
	python3 -m database.create
	# if postgres: use username, passwords and host from const.py
	# docker run --name=arboreum_backend -e POSTGRES_USER=MwJ59dpuQT4ypdnXt -e POSTGRES_PASSWORD=Fj01gToHm4uv4f1LpBdvZn1RSR8wOWuRTClxBkdw4VQGKm0 -e POSTGRES_DB=arboreum_backend -p  5433:5432 -d postgres:12

