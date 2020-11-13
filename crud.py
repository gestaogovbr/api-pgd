from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
import models, schemas

def get_plano_trabalho(db: Session, cod_plano: int):
    "Traz um plano de trabalho a partir do banco de dados."
    return (
        db
        .query(models.PlanoTrabalho)
        .filter(models.PlanoTrabalho.cod_plano == cod_plano)
        .first()
    )

def create_plano_tabalho(
    db: Session,
    plano_trabalho: schemas.PlanoTrabalho
    ):
    "Cria um plano de trabalho definido pelo cod_plano."
    # db_plano_trabalho = models.PlanoTrabalho(
    #     **plano_trabalho.dict()
    # )
    plano_trabalho_data = jsonable_encoder(plano_trabalho)
    db_plano_trabalho = PlanoTrabalho(**plano_trabalho_data)
    db.add(db_plano_trabalho)
    db.commit()
    db.refresh(db_plano_trabalho)
    return schemas.PlanoTrabalho.from_orm(db_plano_trabalho)

def update_plano_tabalho(
    db: Session,
    plano_trabalho: schemas.PlanoTrabalho
    ):
    "Atualiza um plano de trabalho definido pelo cod_plano."
    db_plano_trabalho = get_plano_trabalho(db, plano_trabalho.cod_plano)
    for k, v in db_plano_trabalho.__dict__.items():
        if k[0] != '_' and k != 'id':
            setattr(db_plano_trabalho, k, getattr(plano_trabalho, k))
    db.commit()
    db.refresh(db_plano_trabalho)
    return db_plano_trabalho