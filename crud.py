from sqlalchemy.orm import Session

import models, schemas

def get_plano_trabalho(db: Session, plano_id: int):
    "Traz um plano de trabalho a partir do banco de dados."
    return (
        db
        .query(models.PlanoTrabalho)
        .filter(models.PlanoTrabalho.id == plano_id)
        .first()
    )

def create_plano_tabalho(
    db: Session,
    plano_id: int,
    plano_trabalho: schemas.PlanoTrabalho
    ):
    "Cria um plano de trabalho definido pelo plano_id."
    db_plano_trabalho = models.PlanoTrabalho(
        id = plano_id,
        **plano_trabalho.dict()
    )
    db.add(db_plano_trabalho)
    db.commit()
    db.refresh(db_plano_trabalho)
    return db_plano_trabalho

def update_plano_tabalho(
    db: Session,
    plano_id: int,
    plano_trabalho: schemas.PlanoTrabalho
    ):
    "Atualiza um plano de trabalho definido pelo plano_id."
    db_plano_trabalho = get_plano_trabalho(db, plano_id)
    for k, v in db_plano_trabalho.__dict__.items():
        if k[0] != '_' and k != 'id':
            setattr(db_plano_trabalho, k, getattr(plano_trabalho, k))
    db.commit()
    db.refresh(db_plano_trabalho)
    return db_plano_trabalho