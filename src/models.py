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
    ForeignKeyConstraint
)
from sqlalchemy import event, DDL
from sqlalchemy.orm import relationship

from users import Base


class PlanoEntregas(Base):
    "Plano de Entregas da unidade"
    __tablename__ = "plano_entregas"
    cod_SIAPE_instituidora = Column(
        Integer, primary_key=True, index=True, nullable=False
    )
    id_plano_entrega_unidade = Column(
        Integer, primary_key=True, index=True, nullable=False
    )
    data_inicio_plano_entregas = Column(Date, nullable=False)
    data_termino_plano_entregas = Column(Date, nullable=False)
    avaliacao_plano_entregas = Column(Integer)
    data_avaliacao_plano_entregas = Column(Date)
    cod_SIAPE_unidade_plano = Column(Integer, nullable=False)
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    entregas = relationship(
        "PlanoEntregas",
        back_populates="plano_entregas",
        lazy="joined",
        passive_deletes=True,
        cascade="save-update, merge, delete, delete-orphan",
    )
    __table_args__ = (
        UniqueConstraint(
            "cod_SIAPE_instituidora",
            "id_plano_entrega_unidade",
            name="_instituidora_plano_entregas_uc",
        ),
    )

class TipoMeta(enum.Enum):
    absoluto = 1
    percentual = 2


class Entrega(Base):
    "Entrega"
    __tablename__ = "entrega"
    id_entrega = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_plano_entrega_unidade = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
    )
    cod_SIAPE_instituidora = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
    )
    nome_entrega = Column(String, nullable=False)
    meta_entrega = Column(Integer, nullable=False)
    tipo_meta = Column(Integer, Enum(TipoMeta), nullable=False)
    nome_vinculacao_cadeia_valor = Column(String)
    nome_vinculacao_planejamento = Column(String)
    percentual_progresso_esperado = Column(Integer)
    percentual_progresso_realizado = Column(Integer)
    data_entrega = Column(Date, nullable=False)
    nome_demandante = Column(String, nullable=False)
    nome_destinatario = Column(String, nullable=False)
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_plano_entrega_unidade", cod_SIAPE_instituidora],
            ["plano_entregas.id_plano_entrega_unidade","plano_entregas.cod_SIAPE_instituidora"]
        ),
    )

class PlanoTrabalho(Base):
    "Plano de Trabalho do participante"
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
        Integer, ForeignKey("status_participante.cpf_participante"), nullable=False
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
    id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, nullable=False
    )
    id_plano_trabalho_participante = Column(
        Integer,
        ForeignKey("plano_trabalho.id_plano_trabalho_participante"),
        nullable=False,
    )
    tipo_contribuicao = Column(Integer, Enum(TipoContribuicao), nullable=False)
    descricao_contribuicao = Column(String)
    id_entrega = Column(Integer, ForeignKey("entrega.id_entrega"), nullable=False)
    horas_vinculadas = Column(Integer, nullable=False)
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)


class Consolidacao(Base):
    "Consolidação (registro) de execução do Plano de Trabalho"
    __tablename__ = "consolidacao"
    id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, nullable=False
    )
    id_plano_trabalho_participante = Column(
        Integer,
        ForeignKey("plano_trabalho.id_plano_trabalho_participante"),
        nullable=False,
    )
    data_inicio_registro = Column(Date, nullable=False)
    data_fim_registro = Column(Date, nullable=False)
    avaliacao_plano_trabalho = Column(Integer)
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)


class ModalidadesExecucao(enum.Enum):
    presencial = 1
    teletrabalho_parcial = 2
    teletrabalho_integral = 3
    teletrabalho_no_exterior = 4


class StatusParticipante(Base):
    "Status dos Participantes"
    __tablename__ = "status_participante"
    cpf_participante = Column(Integer, primary_key=True, nullable=False)
    participante_ativo_inativo_pgd = Column(Integer, nullable=False)
    matricula_siape = Column(Integer)
    modalidade_execucao = Column(Integer, Enum(ModalidadesExecucao), nullable=False)
    jornada_trabalho_semanal = Column(Integer, nullable=False)
    data_envio = Column(Date, nullable=False)
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
