#!/usr/local/bin/python
"""Bootstraps the FastAPI application, first waiting for the Postgres
database to be up and running.
"""
import os
import time
import argparse

import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

MAX_RETRIES = 120

parser = argparse.ArgumentParser(description=
    'Wait for the database to be responsive and then runs a command.')
parser.add_argument(
    'command_line',
    nargs='+',
    help=('The command to run after the database is online. '
        'Please encase the command in quotes.'))
args = parser.parse_args()
command = ' '.join(args.command_line) # pylint: disable=invalid-name

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

print('Executing command: ', command)
os.system(command)
