"""Definições dos modelos de dados da API que serão persistidos no
banco pelo mapeamento objeto-relacional (ORM) do SQLAlchemy.
"""

import enum
from textwrap import dedent

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import now

from db_config import Base


class PlanoEntregas(Base):
    __tablename__ = "plano_entregas"

    id = Column(Integer, primary_key=True, index=True)
    origem_unidade = Column(
        String,
        nullable=False,
        comment='Código do sistema da unidade: "SIAPE" ou "SIORG"',
    )
    cod_unidade_autorizadora = Column(
        Integer,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema "
            "Integrado de Administração de Recursos Humanos (SIAPE) "
            "corresponde à Unidade de autorização. Referente ao artigo "
            "3º do Decreto nº 11.072, de 17 de maio de 2022. De forma "
            "geral, são os “Ministros de Estado, os dirigentes máximos "
            "dos órgãos diretamente subordinados ao Presidente da "
            "República e as autoridades máximas das entidades”. Em "
            "termos de SIAPE, geralmente é o código Uorg Lv1. O "
            "próprio Decreto, contudo, indica que tal autoridade "
            "poderá ser delegada a dois níveis hierárquicos "
            "imediatamente inferiores, ou seja, para Uorg Lv2 e Uorg "
            "Lv3. Haverá situações, portanto, em que uma unidade do "
            "Uorg Lv1 de nível 2 ou 3 poderá enviar dados diretamente "
            "para API.",
    )
    cod_unidade_instituidora = Column(
        Integer,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema "
            "Integrado de Administração de Recursos Humanos (SIAPE) "
            "corresponde à Unidade de Instituição. A unidade "
            "administrativa prevista no art. 4º do Decreto nº 11.072, "
            "de 2022. Ele deve ser “de nível não inferior ao de "
            "Secretaria ou equivalente”. Pode ser a mesma que a "
            "unidade de autorização.",
    )
    cod_unidade_executora = Column(
        Integer,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema "
        "Integrado de Administração de Recursos Humanos (SIAPE) "
        "corresponde à Unidade de Execução. Qualquer unidade da "
        "estrutura administrativa que tenha plano de entregas "
        "pactuado.",
    )
    id_plano_entrega = Column(
        String, nullable=False, comment="Identificador único do plano de entregas."
    )
    status = Column(
        Integer,
        nullable=False,
        comment=dedent(
            """
            Indica qual o status do plano de entregas.
            O código deve corresponder às seguintes categorias:

            1 - Cancelado
            2 - Aprovado
            3 - Em execução
            4 - Concluído
            5 - Avaliado

            Regras de validação: a categoria "5" só poderá ser usada se
            os campos "avaliacao_plano_entregas" e
            "data_avaliacao_plano_entregas" estiverem preenchidos.

            É obrigatório o envio dos planos nos status "3", "4" e "5".
            Os planos nos demais status não precisam necessariamente ser
            enviados."""
        ),
    )
    data_inicio = Column(
        Date, nullable=False, comment="Data de início da vigência do plano de entregas."
    )
    data_termino = Column(
        Date,
        nullable=False,
        comment="Data de término da vigência do plano de entregas. Deve "
        'ser depois da "data_inicio_plano_entregas".',
    )
    avaliacao = Column(
        Integer,
        comment=dedent(
            """
            Avaliação do plano de entregas pelo nível hierárquico
            superior ao da chefia da unidade de execução, em até
            trinta dias após o término do plano de entregas, em uma
            das seguintes escalas:
            
            I - excepcional: plano de entregas executado com desempenho
            muito acima do esperado;
            II - alto desempenho: plano de entregas executado com
            desempenho acima do esperado;
            III - adequado: plano de entregas executado dentro do
            esperado;
            IV - inadequado: plano de entregas executado abaixo do
            esperado;
            ou V - plano de entregas não executado"""
        ),
    )
    data_avaliacao = Column(
        Date,
        comment="Data em que o nível hierárquico superior ao da chefia da "
        "unidade de execução avaliou o cumprimento do plano de "
        "entregas",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    entregas = relationship(
        "Entregas",
        back_populates="plano_entregas",
        lazy="joined",
        passive_deletes=True,
        cascade="save-update, merge, delete, delete-orphan",
    )
    __table_args__ = (
        UniqueConstraint(
            "cod_unidade_autorizadora",
            "id_plano_entrega_unidade",
            name="_instituidora_plano_entregas_uc",
        ),
    )


class TipoMeta(enum.IntEnum):
    unidade = 1
    percentual = 2


class Entrega(Base):
    "Entrega"
    __tablename__ = "entrega"
    id_entrega = Column(
        String,
        primary_key=True,
        index=True,
        nullable=False,
        comment="Identificador único da entrega",
    )
    entrega_cancelada = Column(
        Boolean,
        nullable=True,
        default=False,
        comment="TRUE se a entrega tiver sido cancelada; FALSE caso contrário. "
        "O valor padrão é FALSE. A ausência do atributo ou NULL deve ser "
        "interpretada como FALSE.",
    )
    nome_entrega = Column(
        String,
        nullable=False,
        comment="Título do produto ou serviço gerado por uma Unidade de Execução, "
        "resultante da contribuição de seus membros.",
    )
    meta_entrega = Column(
        Integer,
        nullable=False,
        comment="Quantidade unitária de produto ou serviço a ser gerado pela "
        "Unidade de Execução; ou Desempenho percentual da geração de entrega "
        "em relação à quantidade, tempo ou qualidade a ser alcançada.",
    )
    tipo_meta = Column(
        String,
        nullable=False,
        comment='Qualificação do tipo da meta: "unidade" ou "percentual"',
    )
    data_entrega = Column(
        Date,
        nullable=False,
        comment="Data em que a meta de entrega será alcançada, no momento do "
        "planejamento.",
    )
    nome_unidade_demandante = Column(
        String,
        nullable=False,
        comment="Nome da unidade que demandou a execução da entrega.",
    )
    nome_unidade_destinataria = Column(
        String,
        nullable=False,
        comment="Nome da unidade destinatária ou beneficiária da entrega.",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    plano_entregas = relationship(
        "PlanoEntregas",
        back_populates="entregas",
        lazy="joined",
    )
    # campos implícitos a partir do relacionamento
    cod_unidade_autorizadora = Column(
        Integer,
        nullable=False,
        comment="cod_unidade_autorizadora do Plano de Entregas (FK)",
    )
    id_plano_entrega = Column(
        String, nullable=False, comment="id_plano_entrega do Plano de Entregas (FK)"
    )
    __table_args__ = (
        ForeignKeyConstraint(
            [cod_unidade_autorizadora, id_plano_entrega],
            [
                "plano_entregas.cod_unidade_autorizadora",
                "plano_entregas.id_plano_entrega",
            ],
        ),
    )
    


class PlanoTrabalho(Base):
    "Plano de Trabalho do participante"
    __tablename__ = "plano_trabalho"

    id = Column(Integer, primary_key=True, index=True)
    origem_unidade = Column(
        String,
        nullable=False,
        comment="Código do sistema da unidade: \"SIAPE\" ou \"SIORG\".",
    )
    cod_unidade_autorizadora = Column(
        Integer,
        nullable=False,
        comment="""
        Código da unidade organizacional (UORG) no Sistema
        Integrado de Administração de Recursos Humanos (Siape)
        corresponde à Unidade de autorização. Referente ao artigo
        3º do Decreto nº 11.072, de 17 de maio de 2022. De forma
        geral, são os "Ministros de Estado, os dirigentes máximos
        dos órgãos diretamente subordinados ao Presidente da
        República e as autoridades máximas das entidades". Em
        termos de SIAPE, geralmente é o código Uorg Lv1. O
        próprio Decreto, contudo, indica que tal autoridade
        poderá ser delegada a dois níveis hierárquicos
        imediatamente inferiores, ou seja, para Uorg Lv2 e Uorg
        Lv3. Haverá situações, portanto, em que uma unidade do
        Uorg Lv1 de nível 2 ou 3 poderá enviar dados diretamente
        para API.
        """,
    )
    id_plano_trabalho = Column(
        String, nullable=False, comment="Identificador único do plano de trabalho."
    )
    status = Column(
        Integer,
        nullable=False,
        comment="""
        Indica qual o status do plano de trabalho. O código deve
        corresponder às seguintes categorias:

        Cancelado
        Aprovado
        Em execução
        Concluído

        O status "2" refere-se ao inciso II do art. 17 da IN nº 24/2023,
        ou seja, com a pactuação entre chefia e participante do plano
        de trabalho.
        O status "3" refere-se ao art. 20 da IN SEGES-SGPRT/MGi nº 24/2022
        O status "4" (Concluído) indica que os registros de execução do
        plano de trabalho foram inseridos e encaminhados para avaliação.

        Regras de validação: É obrigatório o envio dos planos nos status
        "3" e "4". Os planos nos demais status não precisam
        necessariamente ser enviados.
        """,
    )
    cod_unidade_executora = Column(
        Integer,
        nullable=False,
        comment="""
        Código da unidade organizacional (UORG) no Sistema
        Integrado de Administração de Recursos Humanos (SIAPE)
        corresponde à Unidade de Execução. Qualquer unidade da
        estrutura administrativa que tenha plano de entregas
        pactuado.
        """,
    )
    cpf_participante = Column(
        String,
        nullable=False,
        comment="Número do CPF do participante responsável pelo plano de trabalho.",
    )
    matricula_siape = Column(
        String,
        nullable=False,
        comment="Número da matrícula do participante no Sistema Integrado de "
        "Administração de Recursos Humanos (SIAPE).",
    )
    data_inicio = Column(
        Date,
        nullable=False,
        comment="Data de início do plano de trabalho do participante. "
        "Regras de validação: deve ser posterior à \"data_assinatura_tcr\" "
        "e à \"data_inicio\" do \"plano_entregas\".",
    )
    data_termino = Column(
        Date,
        nullable=False,
        comment="Data de término do plano de trabalho do participante. "
        "Regras de validação: deve ser posterior à \"data_inicio\".",
    )
    carga_horaria_disponivel = Column(
        Integer,
        nullable=False,
        comment="Carga horária total do participante disponível no período de "
        "vigência do plano de trabalho. Não inclui períodos de férias, "
        "ocorrências e afastamentos.",
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
    avaliacao_registros_execucao = relationship(
        "AvaliacaoRegistrosExecucao",
        back_populates="plano_trabalho",
        lazy="joined",
        passive_deletes=True,
        cascade="save-update, merge, delete, delete-orphan",
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
    id_plano_entrega_unidade = Column(
        Integer, nullable=True
    )  # se tipo_contribuicao != 1
    id_entrega = Column(
        Integer,
        nullable=True,  # se tipo_contribuicao != 1
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

    id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, nullable=False
    )

    cod_SIAPE_instituidora = Column(
        Integer,
        index=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no "
        "Sistema Integrado de Administração de Recursos Humanos "
        "(Siape) corresponde à Unidade de Instituição",
    )
    cpf_participante = Column(
        String,
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
        String,
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
    data_envio = Column(  # TODO: verificar descrição e relação com data_insercao
        Date,
        nullable=False,
        comment="Timestamp do envio dos dados pelo órgão ou entidade via API "
        "(Application Programming Interface) para o Órgão Central do SIORG. "
        "Cada envio é completo e não substitui envios anteriores; portanto, "
        "não há uma chave para atualização.",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)


class Users(Base):
    "Usuário da api-pgd"
    __tablename__ = "users"
    id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, nullable=False
    )
    email = Column(
        String,
        nullable=False,
        unique=True,
        comment="Email para login no formato eu@foo.org",
    )
    password = Column(
        String,
        nullable=False,
        comment="Password",
    )
    is_admin = Column(
        Boolean,
        nullable=False,
        default=False,
        comment=(
            "Se tem poderes especiais na api-pgd: cadastro de usuários, "
            "lê grava dados em qualquer unidade, etc."
        ),
    )
    disabled = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Se usuário está inativado",
    )
    cod_unidade_autorizadora = Column(
        Integer,
        nullable=False,
        # default=False,
        comment="Em qual unidade autorizadora o usuário está cadastrado",
    )
    data_atualizacao = Column(
        DateTime,
        onupdate=now(),
    )
    data_insercao = Column(
        DateTime,
        nullable=False,
        default=now(),
    )
