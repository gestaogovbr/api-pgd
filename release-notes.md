# Release notes

## Latest changes

In preparation for version 0.2.0:

* Update environment to `python` 3.11.4
* Update packages: `fastapi` 0.103.0,  12.1.0, `pytest` 7.4.0,
  `sqlalchemy` 2.0.19, `pydantic` >=2
* Remove packages no longer used: `fastapi-users` (replaced by Fief),
  `fastapi-mail`
* Replace `requests` package with `httpx` (offers async support)
* User management now done by Fief application
