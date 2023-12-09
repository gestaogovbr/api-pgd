.PHONY: up
up:
	docker compose up -d --wait

.PHONY: down
down:
	docker compose down

.PHONY: tests
tests:
	docker compose up -d --wait && docker compose exec -T api-pgd sh -c "cd /api-pgd/tests && pytest -vvv --color=yes"

# example: make test TEST_FILTER=test_put_participante_missing_mandatory_fields
# command `$ make test TEST_FILTER="test_put_participante_missing_mandatory_fields"`
.PHONY: test
test:
	docker compose up -d --wait && docker compose exec api-pgd sh -c "cd /api-pgd/tests && pytest -k $(TEST_FILTER) -vvv --color=yes"

.PHONY: build
build:
	docker compose down ; docker rmi ghcr.io/gestaogovbr/api-pgd:latest-dev --force ; docker build --rm -t ghcr.io/gestaogovbr/api-pgd:latest-dev -f Dockerfile.dev .


