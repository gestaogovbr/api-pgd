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

def create_plano_tabalho(db: Session, plano_trabalho: schemas.PlanoTrabalho):
    "Cria um plano de trabalho no banco de dados."
    db_plano_trabalho = models.PlanoTrabalho(**plano_trabalho.dict())
    db.add(db_plano_trabalho)
    db.commit()
    db.refresh(db_plano_trabalho)
    return db_plano_trabalho