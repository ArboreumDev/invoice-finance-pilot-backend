dev-server:
	cd server; uvicorn main:app --reload --port 8000 --host 0.0.0.0

dev-webapp:
	cd webapp; yarn dev

lint:
	echo TODO

test: 
	echo TODO