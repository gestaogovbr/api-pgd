import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event, DDL
from sqlalchemy import Table

SQLALCHEMY_DATABASE_URL = os.environ['SQLALCHEMY_DATABASE_URL']

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

func = DDL("""
    CREATE OR REPLACE FUNCTION insere_data_registro()
    RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                new.data_insercao = current_timestamp;
                RETURN NEW;    
            ELSEIF (TG_OP = 'UPDATE') THEN
                new.data_atualizacao = current_timestamp;
                RETURN NEW;
            END IF;
        END;
    $$ LANGUAGE PLPGSQL
"""
)

event.listen(
    Table,
    'after_create',
    func.execute_if(dialect='postgresql')
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

