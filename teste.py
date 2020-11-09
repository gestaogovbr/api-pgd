import sqlalchemy as sa
engine = sa.create_engine('postgresql://postgres:postgres@db:5432/api_pgd')

with engine.connect() as connection:
    result = connection.execute("select * from teste")
    for row in result:
        print("col1:", row['col1'])

