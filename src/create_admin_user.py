import os

from db_config import async_session_maker
from crud_auth import get_password_hash, get_user
from models import Users

API_PGD_ADMIN_USER = os.environ.get("API_PGD_ADMIN_USER")
API_PGD_ADMIN_PASSWORD = os.environ.get("API_PGD_ADMIN_PASSWORD")


async def init_user_admin():
    db_session = async_session_maker()

    if not await get_user(db_session=db_session, email=API_PGD_ADMIN_USER):
        new_user = Users(
            email=API_PGD_ADMIN_USER,
            # b-crypt
            password=get_password_hash(API_PGD_ADMIN_PASSWORD),
            is_admin=True,
            cod_SIAPE_instituidora=1,
        )

        async with db_session as session:
            session.add(new_user)
            await session.commit()
        print(f"API_PGD_ADMIN:  Usuário administrador `{API_PGD_ADMIN_USER}` criado")
    else:
        print(f"API_PGD_ADMIN:  Usuário administrador `{API_PGD_ADMIN_USER}` já existe")
