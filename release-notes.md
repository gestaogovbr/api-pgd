# Release notes

# 3.3.9
* Aumenta o pool size limit de conexões do SqlAlchemy e refatora método especial (aexit) do DbContextManager

# 3.3.8
* Aumenta o pool size limit de conexões do SqlAlchemy e refatora a classe DbContextManager

## 3.3.7
* Pin bcrypt version for compatibility with passlib 1.7.4
* Allow updating PT and PE upper to 1 year if data_inicio is below the cutoff (31-05-2025)

## 3.3.6
* Add audit table for registering database operations (INSERT/UPDATE/DELETE)
* Hotfix: Refactor update_planos to ensure proper transaction handling 

## 3.3.5
* Use transaction mode in update_plano_trabalho and update_plano_entregas

## 3.3.4
* Split Schema PlanoTrabalhoSchema in PlanoTrabalhoSchema (with validation) and
  PlanoTrabalhoResponseSchema(without validation - for get responses)
* Split Schema PlanoEntregasSchema in PlanoEntregasSchema (with validation)
  and PlanoEntregasResponseSchema(without validation - for get responses)

## 3.3.3
* Reject data_inicio from Plano de trabalho and TCR signature before 2023-07-31

## 3.3.2
* Implement length validation for cod_unidade_autorizadora based on origem_unidade
* Restrict future date for data_avaliacao_registros_execucao
* Create validation for empty Contribuicoes list, on submitting Plano de Trabalho,
  except when the status equals 1.

## 3.3.1
* Fix `Plano de Trabalho` and `Plano de Entrega` validation
to reject plans that overlap a year

## 3.3.0

* Remove validation rule for `data_assinatura_tcr`
  if greater than `data_inicio` of `Plano de Trabalho`
* Update remaining unit's type from Integer to BigInteger
* Remove the --reload flag during image build
* Allow `meta_entrega` to exceed 100 when in percent mode
* Add validation to reject empty `Entregas` on submitting
  `Plano de Entregas`, except when the status equals 1.


## 3.2.8

* Add folder for schema migration scripts
* Add validation rule for `data_inicio` and `data_assinatura_tcr` in
  `PlanoTrabalhoSchema`


## 3.2.7

* Change data type of all columns about units to BigInteger


## 3.2.6

* Allow user to GET their own user data
* Add a robots.txt file and allow indexing only of documentation
* Change mutable list defaults in Pydantic to default factory lists
* Add tests for empty entregas lists
* Handle several database outage situations gracefully, add database
  health check endpoint


## 3.2.5

* Set default access token expiration time to 30 minutes
* Remove "id" field from Contribuicao's Pydantic schema (there is already
  an "id_contribuicao" field)
* Add Content-Security-Policy header to API documentation pages (/docs for
  Swagger UI and /redoc for Redoc)
* Add links to Swagger UI and Redoc versions of the API documentation in
  the API description


## 3.2.4

* Check input of participante, plano_entregas and plano_trabalho for
  possible integers out of allowed range in the database type
* Restrict the status of plano_trabalho to 1, 2, 3 or 4, as in the docs
* Simplify validation of domain based integers
* Solve pydantic's warnings about deprecated use of methods .json and
  .dict
* Solve SQL Alchemy's warnings about absence of PlanoTrabalho in session,
  in context of the relationship with Participante
* Better explain validation of data_assinatura_tcr
* Update allowed values for modalidade_execucao in the docs
* Fix API usage examples in the docs


## 3.2.3

* Handle error when submitting a PUT for plano_trabalho with a json
  value of null in the optional fields that are lists. It is now allowed
  and handled properly


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
