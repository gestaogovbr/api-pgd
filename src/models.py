"""Definições dos modelos de dados da API que serão persistidos no
banco pelo mapeamento objeto-relacional (ORM) do SQLAlchemy.
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
    ForeignKeyConstraint,
)
from sqlalchemy import event, DDL
from sqlalchemy.orm import relationship

from db_config import Base


class PlanoEntregas(Base):
    "Plano de Entregas da unidade"
    __tablename__ = "plano_entregas"
    cod_SIAPE_instituidora = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no "
                "Sistema Integrado de Administração de Recursos Humanos"
                "(Siape) corresponde à Unidade de Instituição",
    )
    id_plano_entrega_unidade = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Identificador único do plano de entregas",
    )
    cancelado = Column(
        Boolean,
        comment="TRUE se o plano tiver sido cancelado; FALSE caso contrário. "
                "O valor padrão é FALSE. A ausência do atributo ou NULL "
                "deve ser interpretada como FALSE."
    )
    data_inicio_plano_entregas = Column(
        Date,
        nullable=False,
        comment="Data de início da vigência do plano de entregas da"
                "Unidade de Execução",
    )
    data_termino_plano_entregas = Column(
        Date,
        nullable=False,
        comment="Data de término da vigência do plano de entregas da"
                "Unidade de Execução",
    )
    avaliacao_plano_entregas = Column(
        Integer,
    comment="Avaliação do plano de entregas pelo nível hierárquico "
            "superior ao da chefia da unidade de execução, em até trinta "
            "dias após o término do plano de entregas, em uma das seguintes "
            "escalas:\n\n\n"
            "I - excepcional: plano de entregas executado com "
            "desempenho muito acima do esperado;\n\n"
            "II - alto desempenho: "
            "plano de entregas executado com desempenho acima do esperado;\n\n"
            "III - adequado: plano de entregas executado dentro do esperado;\n\n"
            "IV - inadequado: plano de entregas executado abaixo do esperado;\n\n"
            "ou V - plano de entregas não executado"
    )
    data_avaliacao_plano_entregas = Column(
        Date,
        comment="Data em que o nível hierárquico superior ao da chefia "
                "da unidade de execução avaliou o cumprimento do plano de "
                "entregas",
    )
    cod_SIAPE_unidade_plano = Column(
        Integer,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema "
                "Integrado de Administração de Recursos Humanos (Siape) "
                "corresponde à Unidade de Execução"
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    entregas = relationship(
        "Entrega",
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


class TipoMeta(enum.IntEnum):
    absoluto = 1
    percentual = 2


class Entrega(Base):
    "Entrega"
    __tablename__ = "entrega"
    id_entrega = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        autoincrement=True,
        comment="Identificador único da entrega",
    )
    id_plano_entrega_unidade = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Identificador único do plano de entregas"
    )
    cod_SIAPE_instituidora = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no "
                "Sistema Integrado de Administração de Recursos Humanos "
                "(Siape) corresponde à Unidade de Instituição",
    )
    nome_entrega = Column(
        String,
        nullable=False,
        comment="Título do produto ou serviço gerado por uma Unidade "
                "de Execução, resultante da contribuição de seus membros",
    )
    meta_entrega = Column(
        Integer,
        nullable=False,
        comment="Quantidade unitária de produto ou serviço a ser gerado "
                "pela Unidade de Execução; ou Desempenho percentual da geração "
                "de entrega em relação à quantidade, tempo ou qualidade a ser "
                "alcançada",
    )
    tipo_meta = Column(
        Integer,
        Enum(TipoMeta),
        nullable=False,
        comment="Qualificação do tipo da meta: unidade ou percentual"
    )
    nome_vinculacao_cadeia_valor = Column(
        String,
        comment="Nome do processo da cadeia de valor da instituição no "
                "qual a entrega se vincula diretamente",
    )
    nome_vinculacao_planejamento = Column(
        String,
        comment="Nome do item mais próximo do planejamento da instituição "
                "no qual a entrega se vincula diretamente",
    )
    percentual_progresso_esperado = Column(
        Integer,
        comment="Percentual de execução da meta da entrega a ser alcançado "
                "no prazo de vigência do plano de entregas. Indica o nível de "
                "progresso esperado em relação à meta definida",
    )
    percentual_progresso_realizado = Column(
        Integer,
        comment="Percentual de execução da meta da entrega alcançado no "
                "prazo de vigência do plano de entregas. Indica o nível de "
                "progresso alcançado em relação à meta definida",
    )
    data_entrega = Column(
        Date,
        nullable=False,
        comment="Data em que a meta de entrega será alcançada",
    )
    nome_demandante = Column(
        String,
        nullable=False,
        comment="Nome da unidade que demandou a execução da entrega",
    )
    nome_destinatario = Column(
        String,
        nullable=False,
        comment="Nome do destinatário ou beneficiário da entrega",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    plano_entregas = relationship(
        "PlanoEntregas",
        back_populates="entregas",
        lazy="joined",
    )
    __table_args__ = (
        ForeignKeyConstraint(
            [id_plano_entrega_unidade, cod_SIAPE_instituidora],
            [
                "plano_entregas.id_plano_entrega_unidade",
                "plano_entregas.cod_SIAPE_instituidora",
            ],
        ),
    )


class PlanoTrabalho(Base):
    "Plano de Trabalho do participante"
    __tablename__ = "plano_trabalho"
    cod_SIAPE_instituidora = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no "
                "Sistema Integrado de Administração de Recursos Humanos "
                "(Siape) corresponde à Unidade de Instituição",
    )
    id_plano_trabalho_participante = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Identificador único do plano de trabalho",
    )
    cancelado = Column(
        Boolean,
        comment="TRUE se o plano tiver sido cancelado; FALSE caso contrário. "
                "O valor padrão é FALSE. A ausência do atributo ou NULL "
                "deve ser interpretada como FALSE."
    )
    id_plano_entrega_unidade = Column(
        Integer,
        nullable=False,
        comment="Identificador único do plano de entregas",
    )
    cod_SIAPE_unidade_exercicio = Column(
        Integer,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema Integrado "
                "de Administração de Recursos Humanos (Siape) onde o participante "
                "se encontra formalmente em exercício",
    )
    cpf_participante = Column(
        Integer,
        ForeignKey("status_participante.cpf_participante"),
        nullable=False,
        comment="Número do CPF do participante responsável pelo "
                "plano de trabalho",
    )
    data_inicio_plano = Column(
        Date,
        nullable=False,
        comment="Data de início da vigência do plano de trabalho do "
                "participante."
    )
    data_termino_plano = Column(
        Date,
        nullable=False,
        comment="Data de término da vigência do plano de trabalho do "
                "participante"
    )
    carga_horaria_total_periodo_plano = Column(
        Integer,
        nullable=False,
        comment="Carga horária útil total do participante disponível no "
                "período de vigência do plano de trabalho. Não inclui "
                "períodos de férias,  ocorrências e afastamentos",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    contribuicoes = relationship(
        "Contribuicao",
        back_populates="plano_trabalho",
        lazy="joined",
        passive_deletes=True,
        cascade="save-update, merge, delete, delete-orphan",
    )
    consolidacoes = relationship(
        "Consolidacao",
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
        ForeignKeyConstraint(
            [id_plano_entrega_unidade, cod_SIAPE_instituidora],
            [
                "plano_entregas.id_plano_entrega_unidade",
                "plano_entregas.cod_SIAPE_instituidora",
            ],
        ),
    )


class TipoContribuicao(enum.IntEnum):
    entrega_propria_unidade = 1
    nao_vinculada = 2
    entrega_outra_unidade = 3


class Contribuicao(Base):
    "Contribuição para um Plano de Trabalho"
    __tablename__ = "contribuicao"
    id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, nullable=False
    )
    cod_SIAPE_instituidora = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no "
                "Sistema Integrado de Administração de Recursos Humanos "
                "(Siape) corresponde à Unidade de Instituição",
        )
    id_plano_trabalho_participante = Column(
        Integer,
        nullable=False,
        comment="Identificador único do plano de trabalho",
    )
    tipo_contribuicao = Column(
        Integer,
        Enum(TipoContribuicao),
        nullable=False,
        comment="Tipos de contribuição que o participante pode realizar: "
                "1 - Contribuição para entrega da própria unidade de execução "
                "do participante; 2 - Contribuição não vinculada diretamente a entrega, "
                "mas necessária ao adequado funcionamento administrativo (por exemplo, "
                "Atividades de apoio, assessoramento e desenvolvimento, e Atividades "
                "de gestão de equipes e entregas); 3 - Contribuição vinculada a "
                "entrega de outra unidade de execução, inclusive de outros órgãos "
                "e entidades",
    )
    descricao_contribuicao = Column(
        String,
        comment="Descrição do conjunto de tarefas e/ou atividades a serem "
                "realizadas no período de vigência do plano de trabalho com o "
                "intuito de contribuir com a execução de determinada entrega",
    )
    id_plano_entrega_unidade = Column(Integer, nullable=False)
    id_entrega = Column(
        Integer,
        nullable=False,
        comment="Identificador único da entrega",
    )
    horas_vinculadas = Column(
        Integer,
        nullable=False,
        comment="Quantidade de horas da carga horária útil total do "
                "participante disponível no período de vigência do plano de "
                "trabalho vinculadas a uma determinada entrega",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    plano_trabalho = relationship(
        "PlanoTrabalho",
        back_populates="contribuicoes",
        lazy="joined",
    )
    __table_args__ = (
        ForeignKeyConstraint(
            [cod_SIAPE_instituidora, id_plano_trabalho_participante],
            [
                "plano_trabalho.cod_SIAPE_instituidora",
                "plano_trabalho.id_plano_trabalho_participante",
            ],
        ),
        ForeignKeyConstraint(
            [cod_SIAPE_instituidora, id_plano_entrega_unidade, id_entrega],
            [
                "entrega.cod_SIAPE_instituidora",
                "entrega.id_plano_entrega_unidade",
                "entrega.id_entrega",
            ],
        ),
    )


class Consolidacao(Base):
    "Consolidação (registro) de execução do Plano de Trabalho"
    __tablename__ = "consolidacao"
    id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, nullable=False
    )
    cod_SIAPE_instituidora = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no "
                "Sistema Integrado de Administração de Recursos Humanos "
                "(Siape) corresponde à Unidade de Instituição",
    )
    id_plano_trabalho_participante = Column(
        Integer,
        nullable=False,
        comment="Identificador único do plano de trabalho",
    )
    data_inicio_registro = Column(
        Date,
        nullable=False,
        comment="Data de início do registro das informações do plano de trabalho",
    )
    data_fim_registro = Column(
        Date,
        nullable=False,
        comment="Data final de registro das informações do plano de trabalho",
    )
    avaliacao_plano_trabalho = Column(
        Integer,
        comment="Avaliação do plano de trabalho do participante pela chefia da "
        "unidade de execução ou a quem ela delegar, em até vinte dias após a "
        "data limite do registro feito pelo participante, em uma das seguintes escalas:\n\n\n"
        "I - excepcional: plano de trabalho executado muito acima do esperado;\n\n"
        "II - alto desempenho: plano de trabalho executado acima do esperado;\n\n"
        "III - adequado: plano de trabalho executado dentro do esperado;\n\n"
        "IV - inadequado: plano de trabalho executado abaixo do esperado ou parcialmente executado;\n\n"
        "V - não executado: plano de trabalho integralmente não executado",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    plano_trabalho = relationship(
        "PlanoTrabalho",
        back_populates="consolidacoes",
        lazy="joined",
    )
    __table_args__ = (
        ForeignKeyConstraint(
            [cod_SIAPE_instituidora, id_plano_trabalho_participante],
            [
                "plano_trabalho.cod_SIAPE_instituidora",
                "plano_trabalho.id_plano_trabalho_participante",
            ],
        ),
    )


class ModalidadesExecucao(enum.IntEnum):
    presencial = 1
    teletrabalho_parcial = 2
    teletrabalho_integral = 3
    teletrabalho_no_exterior = 4


class StatusParticipante(Base):
    "Status dos Participantes"
    __tablename__ = "status_participante"
    cpf_participante = Column(
        Integer,
        primary_key=True,
        nullable=False,
        comment="Número do CPF do participante responsável pelo plano de "
                "trabalho, sem pontos, hífen ou caracteres especiais",
    )
    participante_ativo_inativo_pgd = Column(
        Integer,
        nullable=False,
        comment="Situação do participante no Programa de Gestão e Desempenho "
                "(PGD): 0 - Inativo; 1 - Ativo. Participante ativo é aquele "
                "habilitado para a proposição e/ou execução do plano de trabalho",
    )
    matricula_siape = Column(
        Integer,
        comment="Número da matrícula do participante no Sistema Integrado "
                "de Administração de Recursos Humanos (Siape)",
    )
    modalidade_execucao = Column(
        Integer,
        Enum(ModalidadesExecucao),
        nullable=False,
        comment="Modalidade e regime de execução do trabalho do participante, "
                "restrito a uma das quatro opções: 1 - Presencial; "
                "2 - Teletrabalho Parcial; 3 - Teletrabalho Integral; "
                "4 - Teletrabalho com Residência no Exterior.",
    )
    jornada_trabalho_semanal = Column(
        Integer,
        nullable=False,
        comment="Jornada de trabalho semanal fixada em razão das atribuições "
                "pertinentes aos respectivos cargos dos participantes. "
                "É definida em lei ou contrato.",
    )
    data_envio = Column(
        Date,
        nullable=False,
        comment="Timestamp do envio dos dados pelo órgão ou entidade via API "
                "(Application Programming Interface) para o Órgão Central do SIORG. "
                "Cada envio é completo e não substitui envios anteriores; portanto, "
                "não há uma chave para atualização.",
    )
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
