.PHONY: build
build:
	docker build -t api-pgd .

.PHONY: rebuild
rebuild:
	docker build --rm -t api-pgd .

# Initialize environment variables for development environment
.PHONY: init-env
init-env:
	./init/load_fief_env.sh

# Initialize environment variables for tests in CI/CD
.PHONY: init-env-tests
init-env:
	cp -n ./init/.env.tests .env

# Apply initial configuration to Fief instance (container must be already
# running)
.PHONY: fief-config
fief-config:
	docker compose exec -T web sh -c "cd ./init && python configure_fief.py"

.PHONY: up
up:
	docker compose up -d --wait

.PHONY: down
down:
	docker compose down

.PHONY: tests
tests:
	docker compose exec -T web sh -c "cd /home/api-pgd/tests && pytest -vvv --color=yes"
