#!/usr/local/bin/python
"""
Ferramenta de administração da API-PGD.
"""

# dependências
import os
import argparse
import getpass
import asyncio

import sqlalchemy as sa
from sqlalchemy.sql import text as sa_text

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

from auth import (user_db, User, UserCreate, UserUpdate, UserDB,
                    SECRET_KEY, database_meta)
import crud

jwt_authentication = JWTAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=3600,
    tokenUrl="/auth/jwt/login"
)

fastapi_users = FastAPIUsers(
    user_db,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

def list_users(connection: sa.engine.Connection, cod_unidade: int = None):
    """ Lista os usuários presentes no banco para a unidade COD_UNIDADE.
    Caso seja omitido, mostra os usuários de todas as unidades.
    """
    if cod_unidade is None:
        result = connection.execute("select count(*) from public.user")
    else:
        result = connection.execute(
            "select count(*) from public.user where "
            f"cod_unidade='{cod_unidade}'"
        )
    user_quantity = result.scalar()
    if user_quantity < 1:
        print(
            "Não há usuários cadastrados" +
            (f" na unidade {cod_unidade}" if cod_unidade is not None else "") +
            "."
        )
        return
    plural = "s" if user_quantity > 1 else ""
    print (
        f"Há {user_quantity} usuário{plural} cadastrado{plural}" +
        (f" na unidade {cod_unidade}" if cod_unidade is not None else "") +
        ": \n"
    )
    if cod_unidade is None:
        result = connection.execute("select * from public.user")
    else:
        result = connection.execute(
            "select * from public.user where "
            f"cod_unidade='{cod_unidade}'"
        )
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
    email = email.replace('"', "").replace("'", "")
    user = connection.execute(
        f"select * from public.user where email='{email}'"
    ).fetchone()
    if user is None:
        print(f"Nenhum usuário não encontrado com o e-mail {email}")
        return
    if user["is_superuser"]:
        print(f"Usuário com o e-mail {email} já é superusuário.")
    result = connection.execute(
        "update public.user set is_superuser=true "
        f"WHERE id='{user['id']}'"
    )
    if not result:
        raise IOError ("Erro ao gravar no banco de dados.")
    print(
        "Permissão de superusuário concedida ao usuário "
        f"com o e-mail {email}."
    )

async def create_superuser(
    fastapi_users: FastAPIUsers,
    show_password: bool = False
    ):
    " Cria um novo superusuário."
    print(" Preencha os dados do usuário:\n")
    email = input("  e-mail: ") 
    cod_unidade = input ("  código da unidade: ")
    if show_password:
        password = input("  senha: ")
        confirm_password = input("  confirmação da senha: ")
    else:
        password = getpass.getpass(prompt="  senha: ")
        confirm_password = getpass.getpass(prompt="  confirmação da senha: ")
    if password != confirm_password:
        raise ValueError("As senhas informadas são diferentes.")
    
    await database_meta.connect()
    superuser = await fastapi_users.create_user(
        UserCreate(
            email=email,
            password=password,
            cod_unidade=cod_unidade,
            is_superuser=True
        )
    )
    await database_meta.disconnect()
    if not superuser:
        raise IOError ("Erro ao gravar no banco de dados.")

async def truncate_users(connection: sa.engine.Connection):
    " Expurga todos os usuários do banco de dados."
    connection.execute(sa_text('TRUNCATE TABLE "user"'))
    print("Tabela de usuários truncada.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument(
        "--list_users",
        help=list_users.__doc__,
        nargs="?",
        const=True, # valor quando se usa o argumento sem COD_UNIDADE
        metavar="COD_UNIDADE"
    )
    parser.add_argument(
        "--grant_superuser",
        help=grant_superuser.__doc__,
        nargs=1,
        metavar="USER_EMAIL"
    )
    parser.add_argument(
        "--create_superuser",
        help=create_superuser.__doc__,
        action="store_true"
    )
    parser.add_argument(
        "--show_password",
        help="mostra as senhas ao digitá-las",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--truncate-users",
        help=truncate_users.__doc__,
        action="store_true"
    )

    engine = sa.create_engine(os.environ['SQLALCHEMY_DATABASE_URL'])

    args = parser.parse_args()

    with engine.connect() as connection:
        if args.list_users:
            if args.list_users==True:
                list_users(connection)
            else:
                cod_unidade = args.list_users
                list_users(connection, cod_unidade)
        elif args.grant_superuser:
            grant_superuser(connection, args.grant_superuser.pop())
        elif args.create_superuser:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                create_superuser(fastapi_users, args.show_password)
            )
        elif args.truncate_users:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                truncate_users(connection)
            )
        else:
            parser.print_help()
