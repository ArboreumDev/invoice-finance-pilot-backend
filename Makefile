dev-api:
	uvicorn main:app --reload --port 8000 --host 0.0.0.0

lint:
	flake8 invoice routes test utils --max-line-length=120

lint-format:
	black invoice routes test utils --line-length=120
	autoflake invoice routes test utils --remove-unused-variables --remove-all-unused-imports --in-place -r
	isort invoice routes test utils

test: 
	pytest --workers auto

test_db:
	docker run --name=arboreum_backend -e POSTGRES_USER=MwJ59dpuQT4ypdnXt -e POSTGRES_PASSWORD=Fj01gToHm4uv4f1LpBdvZn1RSR8wOWuRTClxBkdw4VQGKm0 -e POSTGRES_DB=arboreum_backend -p  5432:5432 -d postgres:12
