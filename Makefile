dev-api:
	docker compose --profile testing --profile local-mount --profile local-dev  up -d

dev-api-standalone:
	docker compose -f docker-compose.yml up -d

dev-api-local:
	docker compose --profile testing --profile local-dev up -d db test-db
	uvicorn main:app --app-dir app/ --reload --port 8000 --host 0.0.0.0

lint:
	flake8 app/invoice app/routes app/test app/utils --max-line-length=120

lint-format:
	black app/invoice app/routes app/test app/utils --line-length=120
	autoflake app/invoice app/routes app/test app/utils --remove-unused-variables --remove-all-unused-imports --in-place -r
	isort app/invoice app/routes app/test app/utils

# running tests on docker container but with local files
# TODO to run this change in .env to:
# POSTGRES_TEST_PORT=5432
# POSTGRES_TEST_HOST="test-db"
test:
	docker compose --profile testing --profile local-mount up -d
	docker compose --profile local-mount exec -T backend pytest
	docker compose --profile testing rm -s -v test-db

# running tests on docker container but with files in the container
test-standalone:
	docker compose --profile testing -f docker-compose.yml up -d
	docker compose exec -T backend pytest
	docker compose --profile testing rm -s -v test-db

# running local tests with db as in docker container
test-local:
	docker compose --profile testing up -d test-db
	cd app && python -m pytest
	docker compose --profile testing rm -s -v test-db

test_db:
	docker up arboreum_backend

create_db:
	python3 -m database.create
	# if postgres: use username, passwords and host from const.py
	# docker run --name=arboreum_backend -e POSTGRES_USER=MwJ59dpuQT4ypdnXt -e POSTGRES_PASSWORD=Fj01gToHm4uv4f1LpBdvZn1RSR8wOWuRTClxBkdw4VQGKm0 -e POSTGRES_DB=arboreum_backend -p  5433:5432 -d postgres:12

