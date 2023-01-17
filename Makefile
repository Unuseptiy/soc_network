args := $(wordlist 2, 100, $(MAKECMDGOALS))

APPLICATION_NAME = soc_network
env:
	@$(eval SHELL:=/bin/bash)
	@cp .env.sample .env
	@echo "SECRET_KEY=$$(openssl rand -hex 32)" >> .env

db: ##@Database Create database with docker-compose
	docker-compose -f docker-compose.yml up -d --remove-orphans

migrate:  ##@Database Do all migrations in database
	cd $(APPLICATION_NAME)/db && alembic upgrade $(args)

run:  ##@Application Run application server
	poetry run python3 -m $(APPLICATION_NAME)
