from sqlalchemy.orm import Session
from sqlalchemy.sql import text as sa_text
import models, schemas, util

def get_plano_trabalho(db: Session, cod_unidade: int, cod_plano: str):
    "Traz um plano de trabalho a partir do banco de dados."
    db_plano_trabalho = (
        db
        .query(models.PlanoTrabalho)
        .filter(models.PlanoTrabalho.cod_plano == cod_plano)
        .filter(models.PlanoTrabalho.cod_unidade == cod_unidade)
        .first()
    )
    if db_plano_trabalho:
        return db_plano_trabalho
    else:
        return None

def create_plano_tabalho(
    db: Session,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
    cod_unidade: int
    ):
    "Cria um plano de trabalho definido pelo cod_plano."

    db_atividades = [models.Atividade(**a.dict()) for a in plano_trabalho.atividades]
    for a in db_atividades:
        a.cod_unidade = cod_unidade
    plano_trabalho.atividades = db_atividades
    db_plano_trabalho = models.PlanoTrabalho(
        cod_unidade = cod_unidade,
        **plano_trabalho.dict()
    )
    db.add(db_plano_trabalho)
    db.commit()
    db.refresh(db_plano_trabalho)
    return schemas.PlanoTrabalhoSchema.from_orm(db_plano_trabalho)

def update_plano_trabalho(
    db: Session,
    plano_trabalho: schemas.PlanoTrabalhoSchema,
    cod_unidade: int
    ):
    "Atualiza um plano de trabalho definido pelo cod_plano."

    db_plano_trabalho = (
        db
        .query(models.PlanoTrabalho)
        .filter(models.PlanoTrabalho.cod_plano == plano_trabalho.cod_plano)
        .filter(models.PlanoTrabalho.cod_unidade == cod_unidade)
        .first()
    )
    # db_plano_trabalho.cod_unidade = cod_unidade
    for k, v in plano_trabalho.__dict__.items():
        if k[0] != "_" and k != "atividades":
            setattr(db_plano_trabalho, k, getattr(plano_trabalho, k))
    for atividade in db_plano_trabalho.atividades:
        db.delete(atividade)
    db.commit()
    sa_atividades = [
        models.Atividade(cod_unidade=cod_unidade, **a.dict())
        for a in plano_trabalho.atividades
    ]
    for atividade in sa_atividades:
        db_plano_trabalho.atividades.append(atividade)
    db.commit()
    db.refresh(db_plano_trabalho)
    return db_plano_trabalho

# Following methods only for test purpose

def truncate_pts_atividades(db: Session):
    "Trunca as tabelas principais. Útil para zerar BD para executar testes."
    db.execute(sa_text("TRUNCATE TABLE plano_trabalho CASCADE"))
    db.commit()
