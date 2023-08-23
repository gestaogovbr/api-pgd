.PHONY: build
build:
	docker build -t api-pgd .

.PHONY: rebuild
rebuild:
	docker build --rm -t api-pgd .

.PHONY: fief-init-env
fief-init-env:
	./init/load_fief_env.sh

.PHONY: fief-configure-instance
fief-configure-instance:
	docker exec -it api-pgd_web-1 sh -c "cd ./init && python configure_fief.py"

.PHONY: up
up:
	docker-compose up

.PHONY: down
down:
	docker-compose down

.PHONY: tests
tests:
	docker exec -it api-pgd-web-1 sh -c "cd /home/api-pgd/tests && pytest -vvv --color=yes"