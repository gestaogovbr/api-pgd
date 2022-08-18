#!/usr/local/bin/python
"""Bootstraps the FastAPI application, first waiting for the Postgres
database to be up and running.
"""
import os
import time

import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

MAX_RETRIES = 120
CMD = 'uvicorn api:app --host 0.0.0.0 --port 5057 --reload'

engine = sa.create_engine(os.environ['SQLALCHEMY_DATABASE_URL'])

for _ in range(MAX_RETRIES):
    try:
        with engine.connect() as connection:
            connection.execute("select 'TEST';")
            print('Postgres database found.')
        break
    except OperationalError as e:
        print('Postgres database unavailable, waiting...')
    time.sleep(1)

os.system(CMD)
