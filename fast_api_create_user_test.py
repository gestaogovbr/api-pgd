import asyncio

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

from auth import user_db, User, UserCreate, UserUpdate, UserDB, SECRET_KEY

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

async def create_superuser(fastapi_users: FastAPIUsers):
    superuser = await fastapi_users.create_user(
        UserCreate(
            email="email@example.com",
            password="1234",
            cod_unidade=1,
            is_superuser=True
        )
    )
    return superuser

loop = asyncio.get_event_loop()
loop.run_until_complete(
    create_superuser(fastapi_users)
)
loop.close()