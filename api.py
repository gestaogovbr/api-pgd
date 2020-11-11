from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

import models, schemas, crud
from database import engine, get_db
from auth import (
    fake_users_db, authenticate_user, create_access_token,
    get_current_active_user, oauth2_scheme,
    Token, User
)

ACCESS_TOKEN_EXPIRE_MINUTES = 30

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.put("/plano_trabalho/{plano_id}", response_model=schemas.PlanoTrabalho)
async def create_or_update_plano_trabalho(
    plano_id: int,
    plano_trabalho: schemas.PlanoTrabalho,
    db: Session = Depends(get_db)
    ):
    db_plano_trabalho = crud.get_plano_trabalho(db, plano_id)
    if db_plano_trabalho is None:
        crud.create_plano_tabalho(db, plano_id, plano_trabalho)
    else:
        crud.update_plano_tabalho(db, plano_id, plano_trabalho)
    return plano_trabalho

@app.get("/plano_trabalho/{plano_id}")
def get_plano_trabalho(plano_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    plano_trabalho = crud.get_plano_trabalho(db, plano_id)
    if plano_trabalho is None:
        return HTTPException(404, detail="Plano de trabalho não encontrado")
    return plano_trabalho