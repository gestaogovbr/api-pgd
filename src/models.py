"""Definições dos modelos de dados da API que serão persistidos no
banco pelo ORM do SQLAlchemy.
"""
import enum

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    Float,
    Date,
    DateTime,
    Enum,
    UniqueConstraint,
)
from sqlalchemy import event, DDL
from sqlalchemy.orm import relationship

from users import Base


class PlanoTrabalho(Base):
    "Plano de Trabalho"
    __tablename__ = "plano_trabalho"
    cod_SIAPE_instituidora = Column(
        Integer, primary_key=True, index=True, nullable=False
    )
    id_plano_trabalho_participante = Column(
        Integer, primary_key=True, index=True, nullable=False
    )
    id_plano_entrega_unidade = Column(
        Integer, ForeignKey("plano_entregas.id_plano_entrega_unidade"), nullable=False
    )
    cod_SIAPE_unidade_exercicio = Column(Integer, nullable=False)
    cpf_participante = Column(
        Integer, ForeignKey("participante.cpf_participante"), nullable=False
    )
    data_inicio_plano = Column(Date, nullable=False)
    data_termino_plano = Column(Date, nullable=False)
    carga_horaria_total_periodo_plano = Column(Integer, nullable=False)
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    contribuicoes = relationship(
        "Contribuicao",
        back_populates="plano_trabalho",
        lazy="joined",
        passive_deletes=True,
        cascade="save-update, merge, delete, delete-orphan",
    )
    __table_args__ = (
        UniqueConstraint(
            "cod_SIAPE_instituidora",
            "id_plano_trabalho_participante",
            name="_instituidora_plano_trabalho_uc",
        ),
    )


class TipoContribuicao(enum.Enum):
    entrega_propria_unidade = 1
    nao_vinculada = 2
    entrega_outra_unidade = 3


class Contribuicao(Base):
    "Contribuição para um Plano de Trabalho"
    __tablename__ = "contribuicao"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    id_plano_trabalho_participante = Column(
        Integer,
        ForeignKey("plano_trabalho.id_plano_trabalho_participante"),
        nullable=False,
    )
    tipo_contribuicao = Column(Integer, Enum(TipoContribuicao), nullable=False)
    descricao_contribuicao = Column(String)
    id_entrega = Column(Integer, ForeignKey("Entregas.id_entrega"), nullable=False)
    horas_vinculadas = Column(Integer, nullable=False)
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)


# trigger = DDL("""
#     CREATE TRIGGER inseredata_trigger
#     BEFORE INSERT OR UPDATE ON public.plano_trabalho
#     FOR EACH ROW EXECUTE PROCEDURE insere_data_registro();
# """
# )

# event.listen(
#     PlanoTrabalho.__table__,
#     'after_create',
#     trigger.execute_if(dialect='postgresql')
# )

# trigger = DDL("""
#     CREATE TRIGGER inseredata_trigger
#     BEFORE INSERT OR UPDATE ON public.atividade
#     FOR EACH ROW EXECUTE PROCEDURE insere_data_registro();
# """
# )

# event.listen(
#     Atividade.__table__,
#     'after_create',
#     trigger.execute_if(dialect='postgresql')
# )
