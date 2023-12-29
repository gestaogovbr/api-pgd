from datetime import datetime, timedelta
from typing import Optional, Annotated
import os

from sqlalchemy import select, update
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

import models, schemas
from db_config import DbContextManager


SECRET_KEY = str(os.environ.get("SECRET_KEY"))
ALGORITHM = str(os.environ.get("ALGORITHM"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ## Funções auxiliares


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, str(hashed_password))


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_all_users(
    db_session: DbContextManager,
) -> list[schemas.UsersGetSchema]:
    """Get all users from api database.

    Args:
        db_session (DbContextManager): Session with api database

    Returns:
        list[schemas.UsersGetSchema]: list of users without password
    """

    async with db_session as session:
        result = await session.execute(select(models.Users))
        users = result.scalars().all()

    return [
        schemas.UsersGetSchema(
            **schemas.UsersSchema.model_validate(user).model_dump(exclude=["password"])
        )
        for user in users
    ]


async def get_user(
    db_session: DbContextManager,
    email: str,
) -> Optional[schemas.UsersSchema]:
    async with db_session as session:
        result = await session.execute(select(models.Users).filter_by(email=email))
        user = result.unique().scalar_one_or_none()

    if user:
        return schemas.UsersSchema.model_validate(user)

    return None


async def authenticate_user(db, username: str, password: str):
    user = await get_user(db_session=db, email=username)

    if not user:
        return False

    if not verify_password(password, user.password):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

async def verify_token(token: str, db: DbContextManager):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais não podem ser validadas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = await get_user(db_session=db, email=token_data.username)

    if user is None:
        raise credentials_exception

    return user

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbContextManager = Depends(DbContextManager),
):
    return await verify_token(token, db)

async def get_user_by_token(
    token: str,
    db: DbContextManager = Depends(DbContextManager),
):
    return await verify_token(token, db)


async def get_current_active_user(
    current_user: Annotated[schemas.UsersSchema, Depends(get_current_user)]
) -> Annotated[schemas.UsersSchema, Depends(get_current_user)]:
    """Check if the current user is enabled.

    Raises:
        HTTPException: User with attribute disabled = True
    """

    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Usuário inativo")

    return current_user


async def get_current_admin_user(
    current_user: Annotated[schemas.UsersSchema, Depends(get_current_user)]
):
    """Check if the current user is admin.

    Raises:
        HTTPException: User with attribute is_admin = False
    """

    if not current_user.is_admin:
        raise HTTPException(
            status_code=401, detail="Usuário não tem permissões de administrador"
        )

    return current_user


# ## Crud


async def create_user(
    db_session: DbContextManager,
    user: schemas.UsersSchema,
) -> schemas.UsersSchema:
    """Create user on api database.

    Args:
        db_session (DbContextManager): Session with api database
        user (schemas.UsersSchema): User to be created

    Returns:
        schemas.UsersSchema: Created user
    """

    new_user = models.Users(**user.model_dump())
    # b-crypt
    new_user.password = get_password_hash(new_user.password)
    async with db_session as session:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

    return schemas.UsersSchema.model_validate(new_user)


async def update_user(
    db_session: DbContextManager,
    user: schemas.UsersSchema,
) -> schemas.UsersSchema:
    """Update user on api database.

    Args:
        db_session (DbContextManager): Session with api database
        user (schemas.UsersSchema): User data to be updated

    Returns:
        schemas.UsersSchema: Updated user
    """

    # b-crypt
    user.password = get_password_hash(user.password)
    async with db_session as session:
        await session.execute(
            update(models.Users).filter_by(email=user.email).values(**user.model_dump())
        )
        await session.commit()

    return schemas.UsersSchema.model_validate(user)


async def delete_user(
    db_session: DbContextManager,
    email: str,
) -> str:
    """Delete user on api database.

    Args:
        db_session (DbContextManager): Session with api database
        email (str): email of the user to be deleted

    Raises:
        HTTPException: User does not exist

    Returns:
        str: Message about deletion true or false
    """

    async with db_session as session:
        result = await session.execute(select(models.Users).filter_by(email=email))
        user_to_del = result.unique().scalar_one_or_none()

        if not user_to_del:
            raise HTTPException(status_code=404, detail=f"Usuário `{email}` não existe")

        await session.delete(user_to_del)
        await session.commit()

    return f"Usuário `{email}` deletado"

async def user_reset_password(db_session: DbContextManager, 
                              token: str,
                              new_password: str) -> str:
    """Reset password of a user by passing a access token.

    Args:
        db_session (DbContextManager): Session with api database
        token (str): access token sended by email
        new_password (str): the new password for encryption

    Returns:
        str: Message about updated password
    """    
    

    user = await get_user_by_token(token, db_session)

    user.password = get_password_hash(new_password)

    async with db_session as session:
        await session.execute(
            update(models.Users).filter_by(email=user.email).values(**user.model_dump())
        )
        await session.commit()

    return f"Senha do Usuário {user.email} atualizada"