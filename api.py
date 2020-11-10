from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import models, schemas, crud
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/plano_trabalho/", response_model=schemas.PlanoTrabalho)
async def create_plano_trabalho(
    plano_trabalho: schemas.PlanoTrabalho,
    db: Session = Depends(get_db)
    ):
    crud.create_plano_tabalho(db, plano_trabalho)
    return plano_trabalho

@app.get("/plano_trabalho/{plano_id}")
def get_plano_trabalho(plano_id: int, db: Session = Depends(get_db)):
    plano_trabalho = crud.get_plano_trabalho(db, plano_id)
    if plano_trabalho is None:
        return HTTPException(404, detail="Plano de trabalho não encontrado")
    return plano_trabalho