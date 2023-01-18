args := $(wordlist 2, 100, $(MAKECMDGOALS))

APPLICATION_NAME = soc_network
env:
	@$(eval SHELL:=/bin/bash)
	@cp .env.sample .env.app
	@echo "SECRET_KEY=$$(openssl rand -hex 32)" >> .env.app
	@cp .env.compose.sample .env.app.compose
	@echo "SECRET_KEY=$$(openssl rand -hex 32)" >> .env.app.compose

db: ##@Database Create database with docker
	docker run --name soc-net-db -p 5432:5432 --env-file .env -d postgres:14

migrate:  ##@Database Do all migrations in database
	cd $(APPLICATION_NAME)/db && alembic upgrade $(args)

run:  ##@Application Run application server
	poetry run python3 -m $(APPLICATION_NAME)
