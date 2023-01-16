APPLICATION_NAME = soc_network
env:
	@$(eval SHELL:=/bin/bash)
	@cp .env.sample .env
	@echo "SECRET_KEY=$$(openssl rand -hex 32)" >> .env

db:
	docker-compose -f docker-compose.yml up -d --remove-orphans

run:  ##@Application Run application server
	poetry run python3 -m $(APPLICATION_NAME)
