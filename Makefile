.PHONY: rev migrate

# Создать новую миграцию (Использование: make rev m="added_users_table")
rev:
	docker-compose exec api alembic revision --autogenerate -m "$(m)"

# Накатить миграции до последней
migrate:
	docker-compose exec api alembic upgrade head

# Откатить на одну назад
downgrade:
	docker-compose exec api alembic downgrade -1