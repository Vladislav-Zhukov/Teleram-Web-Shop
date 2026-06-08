up:
	docker compose up -d --build

migrate:
	docker compose exec backend alembic upgrade head

logs-backend:
	docker compose logs -f backend

logs-bot:
	docker compose logs -f bot

logs-web:
	docker compose logs -f web

down:
	docker compose down

reset:
	docker compose down -v
