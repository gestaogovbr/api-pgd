.PHONY: build
build:
	docker build -t api-pgd .

.PHONY: setup
setup: init-fief-env

init-fief-env:
	./init/load_fief_env.sh

configure-fief-instance:
	cd ./init && python configure_fief.py

.PHONY: up
up:
	docker-compose up

.PHONY: down
down:
	docker-compose down

.PHONY: tests
tests:
	docker exec -it api-pgd-web-1 sh -c "cd /home/api-pgd/tests && pytest -vvv --color=yes"
