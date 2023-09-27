.PHONY: build
build:
	docker build -t api-pgd .

.PHONY: rebuild
rebuild:
	docker build --rm -t api-pgd .

.PHONY: init-env
init-env:
	./init/load_fief_env.sh --user-email='test-pgd@nonexisting.gov.br' --user-password='123456*abcdef'

.PHONY: fief-config
fief-config:
	docker compose exec -T web sh -c "cd ./init && python configure_fief.py"

.PHONY: up
up:
	docker compose up

.PHONY: down
down:
	docker compose down

.PHONY: tests
tests:
	docker compose exec -T web sh -c "cd /home/api-pgd/tests && pytest -vvv --color=yes"
