install:
	pip install -r requirements.txt

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

migration:
	alembic revision --autogenerate -m "$(m)"

upgrade:
	alembic upgrade head

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q
