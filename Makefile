dev-server:
	cd server; uvicorn main:app --reload --port 8000 --host 0.0.0.0

dev-webapp:
	cd webapp; yarn dev

lint:
	flake8 server --max-line-length=120

lint-format:
	black server --line-length=120

test: 
	echo TODO