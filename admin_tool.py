#!/usr/local/bin/python
"""
Ferramenta de administração da API-PGD.
"""

# dependências
import argparse
import getpass
import uuid
import sqlalchemy as sa

engine = sa.create_engine('postgresql://postgres:postgres@db-api-pgd:5432/api_pgd')

def list_users(connection: sa.engine.Connection, cod_unidade: int = None):
    """ Lista os usuários presentes no banco para a unidade COD_UNIDADE.
    Caso seja omitido, mostra os usuários de todas as unidades.
    """
    # TODO: implementar filtro de cod_unidade
    if cod_unidade is None:
        result = connection.execute('select count(*) from public.user')
    else:
        result = connection.execute(
            'select count(*) from public.user where '
            f"cod_unidade='{cod_unidade}'"
        )
    user_quantity = result.scalar()
    if user_quantity < 1:
        print(
            'Não há usuários cadastrados'
            ' na unidade' if cod_unidade is not None else ''
            '.'
        )
        return
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
    " Dá permissão de superusuário ao usuário com o e-mail especificado."
    # precaução contra injection
    email = email.replace('"', '').replace("'", "")
    user = connection.execute(
        f"select * from public.user where email='{email}'"
    ).fetchone()
    if user is None:
        print(f'Nenhum usuário não encontrado com o e-mail {email}')
        return
    if user['is_superuser']:
        print(f'Usuário com o e-mail {email} já é superusuário.')
    result = connection.execute(
        'update public.user set is_superuser=true '
        f"WHERE id='{user['id']}'"
    )
    if not result:
        raise IOError ('Erro ao gravar no banco de dados.')
    print(
        'Permissão de superusuário concedida ao usuário '
        f'com o e-mail {email}.'
    )

def hashed(password):
    " Implementar."
    return password

def create_superuser(connection: sa.engine.Connection):
    " Cria um novo superusuário."
    print(' Preencha os dados do usuário:\n')
    email = input('  e-mail: ') 
    cod_unidade = input ('  código da unidade: ')
    password = getpass.getpass(prompt='  senha: ')
    confirm_password = getpass.getpass(prompt='  confirmação da senha: ')
    if password != confirm_password:
        raise ValueError('As senhas informadas são diferentes.')
    user_id = str(uuid.uuid4())
    result = connection.execute(
        'insert into public.user values ' +
        str((user_id, email, hashed(password), True, True, cod_unidade))
    )
    if not result:
        raise IOError ('Erro ao gravar no banco de dados.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(
        '--list_users',
        help=list_users.__doc__,
        nargs='?',
        const=True, # valor quando se omite o parâmetro
        metavar='COD_UNIDADE'
    )
    parser.add_argument(
        '--grant_superuser',
        help=grant_superuser.__doc__,
        nargs=1,
        metavar='USER_EMAIL'
    )
    parser.add_argument(
        '--create_superuser',
        help=create_superuser.__doc__,
        action='store_true'
    )

    args = parser.parse_args()

    with engine.connect() as connection:
        if args.list_users:
            if args.list_users==True:
                list_users(connection)
            else:
                list_users(connection, args.list_users)
        elif args.grant_superuser:
            grant_superuser(connection, args.grant_superuser.pop())
        elif args.create_superuser:
            create_superuser(connection)
        else:
            parser.print_help()
