# Initialize environment variables
# command `make init-env ARGS="-it"` to set, password and fief_secret
.PHONY: init-env
init-env:
	./init/load_fief_env.py $(ARGS)

.PHONY: up
up:
	docker compose up -d --wait

# Apply initial configuration to Fief instance (container must be already
# running)
# command `make fief-config ARGS="-localhost"` to add localhost uri to development
.PHONY: fief-config
fief-config:
	docker compose exec -T api-pgd sh -c "cd /api-pgd/init && python configure_fief.py $(ARGS)"

.PHONY: down
down:
	docker compose down

.PHONY: tests
tests:
	docker compose exec -T api-pgd sh -c "cd /api-pgd/tests && pytest -vvv --color=yes"

# ### Extra configs
# Build local edited Dockerfile
.PHONY: build
build:
	docker build --rm -t ghcr.io/gestaogovbr/api-pgd:latest-dev -f Dockerfile.dev .

# example: make test TEST_FILTER=test_put_participante_missing_mandatory_fields
TEST_FILTER=test
.PHONY: test
test:
	docker compose exec api-pgd sh -c "cd tests && pytest -k $(TEST_FILTER) -vvv --color=yes"
