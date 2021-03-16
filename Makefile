dev-api:
	cd server; uvicorn main:app --reload --port 8000 --host 0.0.0.0

lint:
	flake8 invoice routes test utils --max-line-length=120

lint-format:
	black invoice routes test utils --line-length=120
	autoflake invoice routes test utils --remove-unused-variables --remove-all-unused-imports --in-place -r
	isort invoice routes test utils

test: 
	pytest --workers auto