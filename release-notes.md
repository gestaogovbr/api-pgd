# Release notes


## 3.2.2

* Handle error when attempting to log in with a non-existing user


## 3.2.1

* Add additional explanation about cod_unidade_autorizadora in the
  documentation.
* Speed up test suite by changing the scope of fixtures
* Use deep copy in tests to avoid interference in other tests
* Block users that have been disabled from logging in


## 3.2.0

* Make `data_assinatura_tcr` not nullable
* Add new field and instructions in docs to inform system of origin
* Fix OpenAPI documentation to show the HTTP status codes that can actually be returned.
* Change data type of origem_unidade in Pydantic to Enum
* Use lifespan instead of event handler to remove deprecation warning


## 3.1.0

* Solve interference of Participante's `cod_unidade_lotacao` in
  in Plano de Trabalho `cod_unidade_executora`, in corner cases when they're
  not the same
* Add mandatory field `cod_unidade_lotacao_participante` to Plano de
  Trabalho


## 3.0.9

* Updates to documentation
* Add a warning to Swagger page when `TEST_ENVIRONMENT` environment
  variable is set to `True`
* No longer filter `participante` by `cod_unidade_lotacao` when creating
  a `plano_trabalho`
* Handle correctly time-aware datetimes passed as input to `participante`
* Remove `participante` from the Pydantic schema of `plano_trabalho`
  (data must be sent through the `participante` endpoint itself)
* Update `participante` in the database instead of deleting and
  re-inserting it
* Refactor tests for Plano de Trabalho and Participante to use pytest
  classes
* Allow `data_avaliacao_registros_execucao` to be the same as
  `data_inicio_periodo_avaliativo`


## 3.0.0

* Rewrite the API for a completely new data model based on new requisites.
* Update all dependencies to current versions.
* Divide and refactor tests into a separate files, folders and classes.
* Add to documentation an entity diagram of new data model


## 2.2.0

* Remove `DELETE` method from the `/user/{email}` endpoint.
* Add feature to enable users to reset their own passwords though email.
* Documentation:
  - add page on managing users
  - improve instructions on Swagger API description


## 2.1.0

* Change auth from `fief` to bare on `fastapi` (b-encrypted end to end)
* Change python packages:
  - `fastapi==0.103.0` to `fastapi==0.104.1`
  - `pydantic>=2` to `pydantic[email]>=2`
  - `fief-client[fastapi]==0.17.0` to `None`
  - `None` to `python-jose[cryptography]==3.3.0`
  - `None` to passlib[bcrypt]==1.7.4
  - `None` to python-multipart==0.0.6


## 2.0.0

* Implement the new data model for PGD 2.
* Update environment to `python` 3.11.4
* Update packages: `fastapi` 0.103.0, `pytest` 7.4.0,
  `sqlalchemy` 2.0.19, `pydantic` >=2
* Remove packages no longer used: `fastapi-users` (replaced by Fief),
  `fastapi-mail`
* Replace `requests` package with `httpx` (offers async support)
* User management now done by Fief application
