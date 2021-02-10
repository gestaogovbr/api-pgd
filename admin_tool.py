import sqlalchemy as sa
engine = sa.create_engine('postgresql://postgres:postgres@db-api-pgd:5432/api_pgd')

# TODO: usar argparse para criar ferramenta CLI para criar superuser

with engine.connect() as connection:
    list_users(connection)

def list_users(connection: sa.engine.Connection):
    " Lista os usuários presentes no banco. "
    result = connection.execute('select count(*) from public.user')
    user_quantity = result.scalar()
    plural = 's' if user_quantity > 1 else ''
    print (f'Há {user_quantity} usuário{plural} cadastrado{plural}: \n')
    result = connection.execute('select * from public.user')
    for row in result:
        print(f"\tid: {row['id']}")
        print(f"\temail: {row['email']}")
        print(f"\tcod_unidade: {row['cod_unidade']}")
        print(f"\tis_active: {row['is_active']}")
        print(f"\tis_superuser: {row['is_superuser']}")
        print()

def grant_superuser(connection: sa.engine.Connection, email: str):
    " Dá permissão de superusuário ao usuário especificado. "
    # precaução contra injection
    email = email.replace('"', '').replace("'", "")
    user = connection.execute(
        f'select * from public.user where email={email}'
    ).fetchone()
    # TODO: sql update
