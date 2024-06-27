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
    "Plano de Entregas"
    __tablename__ = "plano_entregas"

    id = Column(Integer, primary_key=True, index=True)
    origem_unidade = Column(
        String,
        nullable=False,
        comment="Código do sistema da unidade: “SIAPE” ou “SIORG”",
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
    id_plano_entregas = Column(
        String, nullable=False, comment="Identificador único do plano de entregas."
    )
    status = Column(
        Integer,
        nullable=False,
        comment=dedent(
            """
            Indica qual o status do plano de entregas.
            O código deve corresponder às seguintes categorias:

            1. Cancelado
            2. Aprovado
            3. Em execução
            4. Concluído
            5. Avaliado

            **Regras de validação:** a categoria "5" só poderá ser usada se
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
        "ser depois da “data_inicio_plano_entregas”.",
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
        "Entrega",
        back_populates="plano_entregas",
        lazy="joined",
        passive_deletes=True,
        cascade="save-update, merge, delete, delete-orphan",
    )
    __table_args__ = (
        UniqueConstraint(
            "origem_unidade",
            "cod_unidade_autorizadora",
            "id_plano_entregas",
            name="_instituidora_plano_entregas_uc",
        ),
    )


class TipoMeta(str, enum.Enum):
    unidade = "unidade"
    percentual = "percentual"


class Entrega(Base):
    "Entrega"
    __tablename__ = "entrega"
    id = Column(Integer, primary_key=True, index=True)
    id_entrega = Column(
        String,
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
        comment="Qualificação do tipo da meta: “unidade” ou “percentual”",
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
    # relacionamentos
    plano_entregas = relationship(
        "PlanoEntregas",
        back_populates="entregas",
        lazy="joined",
    )
    # campos implícitos a partir do relacionamento
    origem_unidade = Column(
        String,
        nullable=False,
        comment="origem_unidade do Plano de Entregas (FK)",
    )
    cod_unidade_autorizadora = Column(
        Integer,
        nullable=False,
        comment="cod_unidade_autorizadora do Plano de Entregas (FK)",
    )
    id_plano_entregas = Column(
        String,
        nullable=False,
        comment="id_plano_entregas do Plano de Entregas (FK)",
    )
    __table_args__ = (
        ForeignKeyConstraint(
            [origem_unidade, cod_unidade_autorizadora, id_plano_entregas],
            [
                "plano_entregas.origem_unidade",
                "plano_entregas.cod_unidade_autorizadora",
                "plano_entregas.id_plano_entregas",
            ],
        ),
        UniqueConstraint(
            "origem_unidade",
            "cod_unidade_autorizadora",
            "id_plano_entregas",
            "id_entrega",
            name="_entrega_uc",
        ),
    )


class PlanoTrabalho(Base):
    "Plano de Trabalho do participante"
    __tablename__ = "plano_trabalho"

    # id = Column(Integer, primary_key=True, index=True)
    origem_unidade = Column(
        String,
        primary_key=True,
        nullable=False,
        comment='Código do sistema da unidade: "SIAPE" ou "SIORG".',
    )
    cod_unidade_autorizadora = Column(
        Integer,
        primary_key=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema "
        "Integrado de Administração de Recursos Humanos (Siape) "
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
    id_plano_trabalho = Column(
        String,
        primary_key=True,
        nullable=False,
        comment="Identificador único do plano de trabalho.",
    )
    status = Column(
        Integer,
        nullable=False,
        comment=dedent(
            """
            Indica qual o status do plano de trabalho. O código deve
            corresponder às seguintes categorias:

            1. Cancelado
            2. Aprovado
            3. Em execução
            4. Concluído

            O status "2" refere-se ao inciso II do art. 17 da IN nº 24/2023,
            ou seja, com a pactuação entre chefia e participante do plano
            de trabalho.
            O status "3" refere-se ao art. 20 da IN SEGES-SGPRT/MGi nº 24/2022
            O status "4" (Concluído) indica que os registros de execução do
            plano de trabalho foram inseridos e encaminhados para avaliação.

            **Regras de validação:** É obrigatório o envio dos planos nos status
            "3" e "4". Os planos nos demais status não precisam
            necessariamente ser enviados.
        """
        ),
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
        "\n\n**Regras de validação:** deve ser posterior à “data_assinatura_tcr”"
        "e à “data_inicio” do “plano_entregas”.",
    )
    data_termino = Column(
        Date,
        nullable=False,
        comment="Data de término do plano de trabalho do participante. "
        "\n\n**Regras de validação:** deve ser posterior à “data_inicio”.",
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
    avaliacoes_registros_execucao = relationship(
        "AvaliacaoRegistrosExecucao",
        back_populates="plano_trabalho",
        lazy="joined",
        passive_deletes=True,
        cascade="save-update, merge, delete, delete-orphan",
    )
    participante = relationship(
        "Participante",
        back_populates="planos_trabalho",
        lazy="joined",
    )
    __table_args__ = (
        ForeignKeyConstraint(
            [
                origem_unidade,
                cod_unidade_autorizadora,
                cod_unidade_executora,
                matricula_siape,
            ],
            [
                "participante.origem_unidade",
                "participante.cod_unidade_autorizadora",
                "participante.cod_unidade_lotacao",
                "participante.matricula_siape",
            ],
        ),
        UniqueConstraint(
            "origem_unidade",
            "cod_unidade_autorizadora",
            "id_plano_trabalho",
            name="_plano_trabalho_uc",
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
    id_contribuicao = Column(
        String,
        nullable=False,
        comment="Identificador único da contribuição.",
    )
    # cod_unidade_instituidora = Column(
    #     Integer,
    #     nullable=False,
    #     comment="Código da unidade organizacional (UORG) no Sistema Integrado "
    #     "de Administração de Recursos Humanos (SIAPE) corresponde à Unidade "
    #     "de Instituição.",
    # )
    tipo_contribuicao = Column(
        Integer,
        nullable=False,
        comment=dedent(
            """
            Tipos de contribuição que o participante pode realizar:

            1. Contribuição para entrega da própria unidade de execução
            do participante;
            2. Contribuição não vinculada diretamente a entrega, mas
            necessária ao adequado funcionamento administrativo (por
            exemplo, Atividades de apoio, assessoramento e
            desenvolvimento, e Atividades de gestão de equipes e
            entregas);
            3. Contribuição vinculada a entrega de outra unidade de
            execução, inclusive de outros órgãos e entidades
            """
        ),
    )
    percentual_contribuicao = Column(
        Integer,
        nullable=False,
        comment=dedent(
            """
            Proporção (%) da "carga_horaria_disponivel" vinculada a uma
            determinada contribuição, podendo ser entregas da unidade de
            execução, entregas de outra unidade ou não vinculadas diretamente
            a entregas.

            **Regras de validação:** Deve ser maior que 0 e menor ou igual a 100.
        """
        ),
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    # relacionamentos
    plano_trabalho = relationship(
        "PlanoTrabalho",
        back_populates="contribuicoes",
        lazy="joined",
    )
    # campos implícitos a partir do relacionamento
    origem_unidade_pt = Column(
        String,
        nullable=False,
        comment="Código do sistema da unidade: “SIAPE” ou “SIORG”, referente "
        "ao Plano de Trabalho. (FK)",
    )
    cod_unidade_autorizadora_pt = Column(
        Integer,
        nullable=False,
        comment="cod_unidade_autorizadora do Plano de Trabalho (FK)",
    )
    id_plano_trabalho = Column(
        String,
        nullable=False,
        comment="id_plano_trabalho do Plano de Trabalho (FK)",
    )
    id_plano_entregas = Column(
        String,
        nullable=True,
        comment="Identificador único do plano de entrega ao qual o plano de "
        "trabalho está ligado.",
    )
    id_entrega = Column(
        String,
        nullable=True,
        comment="Identificador único da entrega.",
    )
    __table_args__ = (
        ForeignKeyConstraint(
            [origem_unidade_pt, cod_unidade_autorizadora_pt, id_plano_trabalho],
            [
                "plano_trabalho.origem_unidade",
                "plano_trabalho.cod_unidade_autorizadora",
                "plano_trabalho.id_plano_trabalho",
            ],
        ),
    )


class AvaliacaoRegistrosExecucao(Base):
    "Avaliação de Registros de Execução"
    __tablename__ = "avaliacao_registros_execucao"

    id = Column(
        Integer, primary_key=True, index=True, autoincrement=True, nullable=False
    )
    id_periodo_avaliativo = Column(
        String,
        index=True,
        nullable=False,
        comment="Identificador único do período avaliativo contendo o registro de "
        "execução do plano de trabalho.",
    )
    data_inicio_periodo_avaliativo = Column(
        Date,
        nullable=False,
        comment="Início do período avaliativo. Regras de validação: deve ser "
        "posterior à “data_inicio” do “plano_trabalho”",
    )
    data_fim_periodo_avaliativo = Column(
        Date,
        nullable=False,
        comment="Fim do período avaliativo. Regras de validação: deve ser "
        "posterior à “data_inicio_periodo_avaliativo”",
    )
    avaliacao_registros_execucao = Column(
        Integer,
        nullable=False,
        comment=dedent(
            """
            Avaliação dos registros de execução do plano de trabalho no
            respectivo período avaliativo, em uma das seguintes escalas:

            1. excepcional: plano de trabalho executado muito acima do esperado;
            2. alto desempenho: plano de trabalho executado acima do esperado;
            3. adequado: plano de trabalho executado dentro do esperado;
            4. inadequado: plano de trabalho executado abaixo do esperado ou 
            parcialmente executado;
            5. não executado: plano de trabalho integralmente não executado."""
        ),
    )
    data_avaliacao_registros_execucao = Column(
        Date,
        nullable=False,
        comment="Data em que foi realizada avaliação dos registros de execução do "
        "plano de trabalho no período avaliativo. Regras de validação: deve ser "
        "posterior à “data_inicio_periodo_avaliativo”",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    plano_trabalho = relationship(
        "PlanoTrabalho",
        back_populates="avaliacoes_registros_execucao",
        lazy="joined",
    )
    # campos implícitos a partir do relacionamento
    origem_unidade_pt = Column(
        String,
        nullable=False,
        comment="Código do sistema da unidade: “SIAPE” ou “SIORG”, referente "
        "ao Plano de Trabalho. (FK)",
    )
    cod_unidade_autorizadora_pt = Column(
        Integer,
        nullable=False,
        comment="cod_unidade_autorizadora do Plano de Trabalho (FK)",
    )
    id_plano_trabalho = Column(
        String,
        nullable=False,
        comment="id_plano_trabalho do Plano de Trabalho (FK)",
    )
    __table_args__ = (
        ForeignKeyConstraint(
            [origem_unidade_pt, cod_unidade_autorizadora_pt, id_plano_trabalho],
            [
                "plano_trabalho.origem_unidade",
                "plano_trabalho.cod_unidade_autorizadora",
                "plano_trabalho.id_plano_trabalho",
            ],
        ),
    )


class ModalidadesExecucao(enum.IntEnum):
    presencial = 1
    teletrabalho_parcial = 2
    teletrabalho_integral = 3
    teletrabalho_no_exterior_inc7 = 4
    teletrabalho_no_exterior_par7 = 5


class Participante(Base):
    "Participante"
    __tablename__ = "participante"
    origem_unidade = Column(
        String,
        primary_key=True,
        nullable=False,
        comment='Código do sistema da unidade: "SIAPE" ou "SIORG".',
    )
    cod_unidade_autorizadora = Column(
        Integer,
        primary_key=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema Integrado de "
        "Administração de Recursos Humanos (SIAPE) corresponde à Unidade de "
        "autorização. Referente ao artigo 3º do Decreto nº 11.072, de 17 de "
        'maio de 2022. De forma geral, são os "Ministros de Estado, os '
        "dirigentes máximos dos órgãos diretamente subordinados ao Presidente "
        'da República e as autoridades máximas das entidades". Em termos de '
        "SIAPE, geralmente é o código Uorg Lv1. O próprio Decreto, contudo, "
        "indica que tal autoridade poderá ser delegada a dois níveis "
        "hierárquicos imediatamente inferiores, ou seja, para Uorg Lv2 e Uorg "
        "Lv3. Haverá situações, portanto, em que uma unidade do Uorg Lv1 de "
        "nível 2 ou 3 poderá enviar dados diretamente para API.\n\n"
        'Exemplo: "Ministério da Gestão e da Inovação em Serviços Públicos" '
        'ou "Conselho de Controle de Atividades Financeiras"\n\n'
        "Obs: A instituição que não esteja no SIAPE pode usar o código SIORG.",
    )
    cod_unidade_lotacao = Column(
        Integer,
        primary_key=True,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema Integrado de "
        "Administração de Recursos Humanos (SIAPE) corresponde à unidade de "
        "lotação do participante.\n\n"
        "Obs: A instituição que não esteja no SIAPE pode usar o código SIORG.",
    )
    matricula_siape = Column(
        String,
        primary_key=True,
        nullable=False,
        comment="Número da matrícula do participante no Sistema Integrado de "
        "Administração de Recursos Humanos (SIAPE).",
    )
    cod_unidade_instituidora = Column(
        Integer,
        nullable=False,
        comment="Código da unidade organizacional (UORG) no Sistema Integrado de "
        "Administração de Recursos Humanos (SIAPE) corresponde à Unidade de "
        'Instituição. Pode ser o mesmo que o "cod_unidade_autorizadora".',
    )
    cpf = Column(
        String,
        nullable=False,
        comment="Número do CPF do agente público selecionado para PGD, sem "
        "pontos, hífen ou caracteres especiais.",
    )
    situacao = Column(
        Integer,
        nullable=False,
        comment="Situação do agente público no Programa de Gestão e Desempenho "
        "(PGD):\n\n"
        "0 - Inativo\n"
        "1 - Ativo",
    )
    modalidade_execucao = Column(
        Integer,
        nullable=False,
        comment="Modalidade e regime de execução do trabalho do participante, "
        "restrito a uma das cinco opções:\n\n"
        "1 - Presencial\n"
        "2 - Teletrabalho parcial\n"
        "3 - Teletrabalho integral\n"
        "4 - Teletrabalho com residência no exterior (Dec.11.072/2022, art. 12, VIII)\n"
        "5 - Teletrabalho com residência no exterior (Dec.11.072/2022, art. 12, §7°)\n\n"
        "Regras de validação: Só é possível a escolha de uma das cinco opções.",
    )
    data_assinatura_tcr = Column(
        Date,
        nullable=False,
        comment="Data de assinatura do Termo de Ciência e Responsabilidade (TCR) "
        "referente ao previsto no inciso IV do art. 11 do Decreto 11.072/2022.",
    )
    data_atualizacao = Column(DateTime)
    data_insercao = Column(DateTime, nullable=False)
    planos_trabalho = relationship(
        "PlanoTrabalho",
        back_populates="participante",
        lazy="joined",
    )


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
    origem_unidade = Column(
        String,
        nullable=False,
        comment="Código do sistema da unidade: “SIAPE” ou “SIORG”.",
    )
    cod_unidade_autorizadora = Column(
        Integer,
        nullable=False,
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
