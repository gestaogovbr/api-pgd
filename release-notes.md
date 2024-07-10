# Release notes


## 3.0.0

* Rewrite the API for a completely new data model based on new requisites.


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
