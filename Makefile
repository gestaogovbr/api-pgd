.PHONY: build
build:
	docker build -t api-pgd .

.PHONY: rebuild
rebuild:
	docker build --rm -t api-pgd .

.PHONY: setup
setup: init-fief-env fief-create-db

.PHONY: init-fief-env
init-fief-env:
	./init/load_fief_env.sh

.PHONY: fief-create-db
fief-create-db:
	docker exec -it -u postgres api-pgd-db-api-pgd-1 createdb fief

.PHONY: fief-configure-instance
fief-configure-instance:
	docker exec -it api-pgd-web-1 sh -c "cd ./init && python configure_fief.py

.PHONY: up
up:
	docker-compose up

.PHONY: down
down:
	docker-compose down

.PHONY: tests
tests:
	docker exec -it api-pgd-web-1 sh -c "cd /home/api-pgd/tests && pytest -vvv --color=yes"
