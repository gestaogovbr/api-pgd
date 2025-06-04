"""Módulo que define os esquemas de validação dos dados recebidos pela
API.

A principal ferramenta de validação de dados usada no FastAPI é o
Pydantic: https://docs.pydantic.dev/2.0/
"""

from datetime import date
from enum import Enum, IntEnum
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr
from pydantic import NonNegativeInt, PastDatetime, PositiveInt
from pydantic import model_validator, field_validator

from models import (
    PlanoEntregas,
    Entrega,
    TipoMeta,
    PlanoTrabalho,
    Contribuicao,
    TipoContribuicao,
    AvaliacaoRegistrosExecucao,
    Participante,
    Users,
)
from util import over_a_year

STR_FIELD_MAX_SIZE = 300
NON_NEGATIVE_INT4 = Annotated[NonNegativeInt, Field(le=(2**31) - 1)]
POSITIVE_INT4 = Annotated[PositiveInt, Field(le=(2**31) - 1)]
NON_NEGATIVE_INT8 = Annotated[NonNegativeInt, Field(le=(2**63) - 1)]
POSITIVE_INT8 = Annotated[PositiveInt, Field(le=(2**63) - 1)]

# Funções auxiliares


def cpf_validate(input_cpf: str) -> str:
    """Verifica se um número de CPF em forma de string tem o formato
    esperado e também os dígitos verificadores.

    Args:
        input_cpf (str): O número CPF a ser verificado.

    Raises:
        ValueError: CPF deve conter apenas dígitos.
        ValueError: CPF precisa ter 11 dígitos.
        ValueError: CPF com o mesmo número repetido.
        ValueError: CPF com dígitos verificadores inválidos.

    Returns:
        str: O mesmo que a entrada, se for validado.
    """
    cpf = [int(char) for char in input_cpf if char.isdigit()]

    #  Verifica se o CPF tem todos os números iguais, ex: 111.111.111-11
    #  Esses CPFs são considerados inválidos mas passam na validação dos dígitos
    if len(set(cpf)) == 1:
        raise ValueError("CPF inválido.")

    #  Valida os dois dígitos verificadores
    for i in range(9, 11):
        value = sum((cpf[num] * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != cpf[i]:
            raise ValueError("Dígitos verificadores do CPF inválidos.")

    return input_cpf


# Domínios definidos por Enum


class OrigemUnidadeEnum(str, Enum):
    """Valores permitidos para origem de uma unidade. Determina como
    devem ser interpretados os códigos de unidades. Representa o sistema
    de origem do código.
    """

    siape = "SIAPE"
    siorg = "SIORG"


class SituacaoParticipanteEnum(IntEnum):
    """Valores permitidos para situação de um participante."""

    inativo = 0
    ativo = 1


class ModalidadesExecucao(IntEnum):
    """Modalidade e regime de execução do trabalho do participante."""

    presencial = 1
    teletrabalho_parcial = 2
    teletrabalho_integral = 3
    teletrabalho_no_exterior_inc7 = 4
    teletrabalho_no_exterior_par7 = 5


class StatusPlanoEntregasEnum(IntEnum):
    """Status do Plano de Entregas"""

    cancelado = 1
    aprovado = 2
    em_execucao = 3
    concluido = 4
    avaliado = 5


class StatusPlanoTrabalhoEnum(IntEnum):
    """Status do Plano de Trabalho"""

    cancelado = 1
    aprovado = 2
    em_execucao = 3
    concluido = 4


# Classes de esquemas Pydantic
class OrigemUnidadeValidation(BaseModel):
    @staticmethod
    def must_be_valid_cod_unit(origem: OrigemUnidadeEnum, cod_unidade):
        """Valida o código da unidade de acordo com a origem."""
        if origem == OrigemUnidadeEnum.siape:
            if (
                len(str(cod_unidade)) > 5 and len(str(cod_unidade)) != 14
            ) or cod_unidade < 1:
                raise ValueError("cod_SIAPE inválido")
        elif origem == OrigemUnidadeEnum.siorg:
            if len(str(cod_unidade)) > 6 or cod_unidade < 1:
                raise ValueError("cod_SIORG inválido")


class ContribuicaoSchema(BaseModel):
    __doc__ = Contribuicao.__doc__
    model_config = ConfigDict(from_attributes=True)

    id_contribuicao: str = Field(
        title="Identificador único da contribuição",
        description=Contribuicao.id_contribuicao.comment,
    )
    tipo_contribuicao: TipoContribuicao = Field(
        title="Tipo de contribuição",
        description=Contribuicao.tipo_contribuicao.comment,
    )
    percentual_contribuicao: int = Field(
        title="Percentual de contribuição",
        description=Contribuicao.percentual_contribuicao.comment,
    )
    id_plano_entregas: Optional[str] = Field(
        default=None,
        title="Identificador único do plano de entrega",
        description=Contribuicao.id_plano_entregas.comment,
    )
    id_entrega: Optional[str] = Field(
        default=None,
        title="Identificador único da entrega",
        description=Contribuicao.id_entrega.comment,
    )

    @field_validator("tipo_contribuicao")
    @staticmethod
    def validate_tipo_contribuicao(tipo_contribuicao: TipoContribuicao):
        "Valida se o tipo de contribuição é válido (entre 1 e 3)."
        if tipo_contribuicao not in set(TipoContribuicao):
            raise ValueError("Tipo de contribuição inválido; permitido: 1 a 3")
        return tipo_contribuicao

    @model_validator(mode="after")
    def validate_tipo_contribuicao_entrega_outra_unidade(self) -> "ContribuicaoSchema":
        """Valida se os valores dos campos:

        - id_plano_entregas
        - id_entrega

        estão em conformidade com as regras definidas para campo
        tipo_contribuicao.
        """
        if (self.tipo_contribuicao == TipoContribuicao.entrega_propria_unidade) and (
            getattr(self, "id_plano_entregas", None) is None
            or getattr(self, "id_entrega", None) is None
        ):
            raise ValueError(
                "Os campos id_plano_entregas e id_entrega são obrigatórios "
                "quando tipo_contribuicao == 1. "
                "Valores informados: "
                f"id_plano_entregas == {self.id_plano_entregas}, "
                f"id_entrega == {self.id_entrega}."
            )
        if (self.tipo_contribuicao == TipoContribuicao.nao_vinculada) and (
            getattr(self, "id_plano_entregas", None) is not None
            or getattr(self, "id_entrega", None) is not None
        ):
            raise ValueError(
                "Os campos id_plano_entregas e id_entrega não podem conter "
                "valores quando tipo_contribuicao == 2. "
                "Valores informados: "
                f"id_plano_entregas == {self.id_plano_entregas}, "
                f"id_entrega == {self.id_entrega}."
            )
        return self

    @field_validator("percentual_contribuicao")
    @staticmethod
    def validate_percentual_contribuicao(percentual_contribuicao: int):
        "Valida se o percentual de contribuição está entre 0 e 100."
        if percentual_contribuicao < 0 or percentual_contribuicao > 100:
            raise ValueError("O percentual de contribuição deve estar entre 0 e 100.")
        return percentual_contribuicao


class AvaliacaoRegistrosExecucaoSchema(BaseModel):
    __doc__ = AvaliacaoRegistrosExecucao.__doc__
    model_config = ConfigDict(from_attributes=True)

    id_periodo_avaliativo: str = Field(
        title="Identificador do período avaliativo",
        description=AvaliacaoRegistrosExecucao.id_periodo_avaliativo.comment,
    )
    data_inicio_periodo_avaliativo: date = Field(
        title="Data de início do período avaliativo",
        description=AvaliacaoRegistrosExecucao.data_inicio_periodo_avaliativo.comment,
    )
    data_fim_periodo_avaliativo: date = Field(
        title="Data de fim do período avaliativo",
        description=AvaliacaoRegistrosExecucao.data_fim_periodo_avaliativo.comment,
    )
    avaliacao_registros_execucao: int = Field(
        title="Avaliação dos registros de execução",
        description=AvaliacaoRegistrosExecucao.avaliacao_registros_execucao.comment,
    )
    data_avaliacao_registros_execucao: date = Field(
        title="Data da avaliação dos registros de execução",
        description=AvaliacaoRegistrosExecucao.data_avaliacao_registros_execucao.comment,
    )

    @field_validator("avaliacao_registros_execucao")
    @staticmethod
    def validate_avaliacao_registros_execucao(value: int) -> int:
        """Valida a avaliação dos registros de execução."""
        if value not in range(1, 6):
            raise ValueError(
                "Avaliação de registros de execução inválida; permitido: 1 a 5"
            )
        return value

    @field_validator("data_avaliacao_registros_execucao")
    @staticmethod
    def validate_data_avaliacao_not_future(data_avaliacao_registros_execucao: date) -> date:
        """Valida se a data de avaliação é inferior ou igual a data de envio."""
        if data_avaliacao_registros_execucao > date.today():
            raise ValueError(
                "A data de avaliação de registros de execução não pode ser "
                "superior à data atual."
            )
        return data_avaliacao_registros_execucao

    @model_validator(mode="after")
    def validate_data_fim_periodo_avaliativo(
        self,
    ) -> "AvaliacaoRegistrosExecucaoSchema":
        """Valida se a data de fim do período avaliativo é posterior à
        data de início do período avaliativo."""
        if self.data_fim_periodo_avaliativo < self.data_inicio_periodo_avaliativo:
            raise ValueError(
                "A data de fim do período avaliativo deve ser igual ou "
                "posterior à data de início do período avaliativo."
            )
        return self

    @model_validator(mode="after")
    def validate_data_avaliacao_data_inicio_periodo_avaliativo(
        self,
    ) -> "AvaliacaoRegistrosExecucaoSchema":
        """Valida se a data de avaliação dos registros de execução é
        posterior à data de início do período avaliativo."""
        if self.data_avaliacao_registros_execucao < self.data_inicio_periodo_avaliativo:
            raise ValueError(
                "A data de avaliação de registros de execução deve ser "
                "igual ou posterior à data de início do período avaliativo."
            )
        return self


class PlanoTrabalhoSchema(BaseModel):
    __doc__ = PlanoTrabalho.__doc__
    model_config = ConfigDict(from_attributes=True)

    origem_unidade: OrigemUnidadeEnum = Field(
        title="Origem da unidade",
        description=PlanoTrabalho.origem_unidade.comment,
    )
    cod_unidade_autorizadora: POSITIVE_INT8 = Field(
        title="Código da unidade autorizadora",
        description=PlanoTrabalho.cod_unidade_autorizadora.comment,
    )
    id_plano_trabalho: str = Field(
        title="Identificador único do plano de trabalho",
        description=PlanoTrabalho.id_plano_trabalho.comment,
    )
    status: StatusPlanoTrabalhoEnum = Field(
        title="Status do plano de trabalho",
        description=PlanoTrabalho.status.comment,
    )
    cod_unidade_executora: POSITIVE_INT8 = Field(
        title="Código da unidade executora",
        description=PlanoTrabalho.cod_unidade_executora.comment,
    )
    cpf_participante: str = Field(
        title="CPF do participante",
        description=PlanoTrabalho.cpf_participante.comment,
        min_length=11,
        max_length=11,
        pattern=r"\d{11}",
    )
    matricula_siape: str = Field(
        title="Matrícula SIAPE do participante",
        description=PlanoTrabalho.matricula_siape.comment,
        min_length=7,
        max_length=7,
        pattern=r"\d{7}",
    )
    cod_unidade_lotacao_participante: POSITIVE_INT8 = Field(
        title="Código da unidade lotacao participante",
        description=PlanoTrabalho.cod_unidade_lotacao_participante.comment,
    )
    data_inicio: date = Field(
        title="Data de início do plano de trabalho",
        description=PlanoTrabalho.data_inicio.comment,
    )
    data_termino: date = Field(
        title="Data de término do plano de trabalho",
        description=PlanoTrabalho.data_termino.comment,
    )
    carga_horaria_disponivel: NON_NEGATIVE_INT4 = Field(
        title="Carga horária disponível do participante",
        description=PlanoTrabalho.carga_horaria_disponivel.comment,
    )
    contribuicoes: List[ContribuicaoSchema] = Field(
        default_factory=list,
        title="Contribuições",
        description="Lista de Contribuições planejadas para o Plano de Trabalho.",
    )
    avaliacoes_registros_execucao: Optional[List[AvaliacaoRegistrosExecucaoSchema]] = (
        Field(
            default_factory=list,
            title="Avaliações de registros de execução",
            description="Lista de avaliações de registros de execução do Plano de Trabalho.",
        )
    )

    @field_validator("cpf_participante")
    @staticmethod
    def cpf_part_validate(cpf_participante: str) -> str:
        """Valida o CPF do participante."""
        return cpf_validate(cpf_participante)

    @model_validator(mode="after")
    def validate_unidade(self):
        OrigemUnidadeValidation.must_be_valid_cod_unit(
            self.origem_unidade, self.cod_unidade_autorizadora
        )
        return self

    @model_validator(mode="after")
    def year_interval(self) -> "PlanoTrabalhoSchema":
        """Garante que o plano não abrange um período maior que 1 ano."""
        if over_a_year(self.data_inicio, self.data_termino) == 1:
            raise ValueError(
                "Plano de trabalho não pode abranger período maior que 1 ano"
            )
        return self

    @model_validator(mode="after")
    def must_be_sequential_dates(self) -> "PlanoTrabalhoSchema":
        "Verifica se a data de início e a data de término estão na ordem esperada."
        if self.data_inicio > self.data_termino:
            raise ValueError(
                "data_termino do Plano de Trabalho deve ser maior "
                "ou igual que data_inicio"
            )
        return self

    # Validações relacionadas às avaliações de registros de execução

    @model_validator(mode="after")
    def validate_data_inicio_periodo_avaliativo(self) -> "PlanoTrabalhoSchema":
        """Valida se a data de início do período avaliativo de cada item
        das avaliacoes_registros_execucao é posterior à data de início do
        Plano de Trabalho."""
        if self.avaliacoes_registros_execucao and any(
            avaliacao_registros_execucao.data_inicio_periodo_avaliativo
            < self.data_inicio
            for avaliacao_registros_execucao in self.avaliacoes_registros_execucao
        ):
            raise ValueError(
                "A data de início do período avaliativo deve ser igual ou "
                "posterior à data de início do Plano de Trabalho."
            )
        return self

    @field_validator("avaliacoes_registros_execucao")
    @staticmethod
    def avaliacoes_not_overlapping(
        avaliacoes: List[List[AvaliacaoRegistrosExecucaoSchema]],
    ):
        """Verifica se há avaliações de execução com sobreposições de datas"""
        if avaliacoes:
            periodo_avaliativo = [
                (
                    avaliacao.data_inicio_periodo_avaliativo,
                    avaliacao.data_fim_periodo_avaliativo,
                )
                for avaliacao in avaliacoes
            ]

            periodo_avaliativo.sort(key=lambda avaliacao: avaliacao[0])

            for avaliacao_1, avaliacao_2 in zip(
                periodo_avaliativo[:-1], periodo_avaliativo[1:]
            ):
                data_fim_periodo_avaliativo_1 = avaliacao_1[1]
                data_inicio_periodo_avaliativo_2 = avaliacao_2[0]
                if data_inicio_periodo_avaliativo_2 < data_fim_periodo_avaliativo_1:
                    raise ValueError(
                        "Uma ou mais avaliações de registros de execução possuem "
                        "data_inicio_periodo_avaliativo e data_fim_periodo_avaliativo "
                        "sobrepostas."
                    )
        return avaliacoes

    @model_validator(mode="after")
    def validate_contribuicoes_not_empty(self) -> "PlanoTrabalhoSchema":
        """Valida se a lista de contribuicoes não está vazia, exceto se
        o status for igual a 1 - Cancelado
        """
        if not self.contribuicoes and self.status != StatusPlanoTrabalhoEnum.cancelado:
            raise ValueError("A lista de contribuições não pode estar vazia")
        return self


class EntregaSchema(BaseModel):
    __doc__ = Entrega.__doc__
    model_config = ConfigDict(from_attributes=True)
    id_entrega: str = Field(
        title="Identificador único da entrega",
        description=Entrega.id_entrega.comment,
    )
    entrega_cancelada: Optional[bool] = Field(
        default=False,
        title="Entrega cancelada",
        description=Entrega.entrega_cancelada.comment,
    )
    nome_entrega: str = Field(
        title="Título da entrega",
        description=Entrega.nome_entrega.comment,
        max_length=STR_FIELD_MAX_SIZE,
    )
    meta_entrega: NonNegativeInt = Field(
        title="Meta estipulada na inclusão no plano",
        description=Entrega.meta_entrega.comment,
    )
    tipo_meta: TipoMeta = Field(
        title="Tipo da meta",
        description=Entrega.tipo_meta.comment,
    )
    data_entrega: date = Field(
        title="Data da entrega",
        description=Entrega.data_entrega.comment,
    )
    nome_unidade_demandante: str = Field(
        title="Nome da unidade demandante",
        description=Entrega.nome_unidade_demandante.comment,
        max_length=STR_FIELD_MAX_SIZE,
    )
    nome_unidade_destinataria: str = Field(
        title="Nome da unidade destinatária",
        description=Entrega.nome_unidade_destinataria.comment,
        max_length=STR_FIELD_MAX_SIZE,
    )


class PlanoEntregasSchema(BaseModel):
    __doc__ = PlanoEntregas.__doc__
    model_config = ConfigDict(from_attributes=True)
    origem_unidade: OrigemUnidadeEnum = Field(
        title="Código do sistema da unidade",
        description=PlanoEntregas.origem_unidade.comment,
    )
    cod_unidade_autorizadora: POSITIVE_INT8 = Field(
        title="Código da unidade autorizadora",
        description=PlanoEntregas.cod_unidade_autorizadora.comment,
    )
    cod_unidade_instituidora: POSITIVE_INT8 = Field(
        title="Código da unidade instituidora",
        description=PlanoEntregas.cod_unidade_instituidora.comment,
    )
    cod_unidade_executora: POSITIVE_INT8 = Field(
        title="Código da unidade executora",
        description=PlanoEntregas.cod_unidade_executora.comment,
    )
    id_plano_entregas: str = Field(
        title="Identificador único do plano de entregas",
        description=PlanoEntregas.id_plano_entregas.comment,
    )
    status: StatusPlanoEntregasEnum = Field(
        title="Status do plano de entregas",
        description=PlanoEntregas.status.comment,
    )
    data_inicio: date = Field(
        title="Data de início do plano de entregas",
        description=PlanoEntregas.data_inicio.comment,
    )
    data_termino: date = Field(
        title="Data de término do plano de entregas",
        description=PlanoEntregas.data_termino.comment,
    )
    avaliacao: Optional[Annotated[PositiveInt, Field(le=5)]] = Field(
        title="Avaliação do plano de entregas",
        description=PlanoEntregas.avaliacao.comment,
    )
    data_avaliacao: Optional[date] = Field(
        title="Data de avaliação do plano de entregas",
        description=PlanoEntregas.data_avaliacao.comment,
    )
    entregas: List[EntregaSchema] = Field(
        default_factory=list,
        title="Entregas",
        description="Lista de entregas associadas ao Plano de Entregas",
    )

    @model_validator(mode="after")
    def validate_entregas_not_empty(self) -> "PlanoEntregasSchema":
        """Valida se a lista de entregas não está vazia, exceto se
        o status for igual a 1 - Cancelado
        """
        if not self.entregas and self.status != StatusPlanoEntregasEnum.cancelado:
            raise ValueError("A lista de entregas não pode estar vazia")
        return self

    @model_validator(mode="after")
    def validate_entregas_uniqueness(self) -> "PlanoEntregasSchema":
        """Valida a unicidade das entregas."""
        # pylint: disable=not-an-iterable
        entregas_ids = [entrega.id_entrega for entrega in self.entregas]
        if len(entregas_ids) != len(set(entregas_ids)):
            raise ValueError("Entregas devem possuir id_entrega diferentes")
        return self

    @model_validator(mode="after")
    def validate_period(self) -> "PlanoEntregasSchema":
        """Valida o período do plano de entregas."""
        if over_a_year(self.data_inicio, self.data_termino) == 1:
            raise ValueError(
                "Plano de entregas não pode abranger período maior que 1 ano"
            )
        if self.data_termino < self.data_inicio:
            raise ValueError("data_termino deve ser maior ou igual que data_inicio.")
        if self.data_avaliacao is not None and self.data_avaliacao < self.data_inicio:
            raise ValueError("data_avaliacao deve ser maior ou igual à data_inicio.")
        return self

    @model_validator(mode="after")
    def validate_status(self) -> "PlanoEntregasSchema":
        """Verifica se o status possui valor válido."""
        if self.status == 5 and (self.avaliacao is None or self.data_avaliacao is None):
            raise ValueError(
                "O status 5 só poderá ser usado se os campos avaliacao e "
                "data_avaliacao estiverem preenchidos."
            )
        return self

    @model_validator(mode="after")
    def validate_unidade(self):
        OrigemUnidadeValidation.must_be_valid_cod_unit(
            self.origem_unidade, self.cod_unidade_autorizadora
        )
        return self


class ParticipanteSchema(BaseModel):
    __doc__ = Participante.__doc__
    model_config = ConfigDict(from_attributes=True)
    origem_unidade: OrigemUnidadeEnum = Field(
        title="Código do sistema da unidade (SIAPE ou SIORG)",
        description=Participante.origem_unidade.comment,
    )
    cod_unidade_autorizadora: NON_NEGATIVE_INT8 = Field(
        title="Código da unidade organizacional autorizadora do PGD",
        description=Participante.cod_unidade_autorizadora.comment,
    )
    cod_unidade_lotacao: NON_NEGATIVE_INT8 = Field(
        title="Código da unidade organizacional de lotação do participante",
        description=Participante.cod_unidade_lotacao.comment,
    )
    matricula_siape: str = Field(
        title="Número da matrícula do participante no SIAPE",
        description=Participante.matricula_siape.comment,
        min_length=7,
        max_length=7,
        pattern=r"\d{7}",
    )
    cod_unidade_instituidora: NON_NEGATIVE_INT8 = Field(
        title="Código da unidade organizacional instituidora do PGD",
        description=Participante.cod_unidade_instituidora.comment,
    )
    cpf: str = Field(
        title="Número do CPF do agente público",
        description=Participante.cpf.comment,
        min_length=11,
        max_length=11,
        pattern=r"\d{11}",
    )
    situacao: SituacaoParticipanteEnum = Field(
        title="Situação do agente público no PGD",
        description=Participante.situacao.comment,
    )
    modalidade_execucao: ModalidadesExecucao = Field(
        title="Modalidade e regime de execução do trabalho",
        description=Participante.modalidade_execucao.comment,
    )
    data_assinatura_tcr: PastDatetime = Field(
        title="Data de assinatura do TCR",
        description=Participante.data_assinatura_tcr.comment,
    )

    @field_validator("matricula_siape")
    @staticmethod
    def matricula_siape_validate(matricula_siape: str) -> str:
        "Valida a matrícula SIAPE do participante."
        if len(set(matricula_siape)) < 2:
            raise ValueError("Matricula SIAPE inválida.")
        return matricula_siape

    @field_validator("cpf")
    @staticmethod
    def cpf_part_validate(cpf: str) -> str:
        "Valida o CPF do participante."
        return cpf_validate(cpf)

    @model_validator(mode="after")
    def validate_unidade(self):
        OrigemUnidadeValidation.must_be_valid_cod_unit(
            self.origem_unidade, self.cod_unidade_autorizadora
        )
        return self


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UsersInputSchema(BaseModel):
    __doc__ = Users.__doc__
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr = Field(
        title="e-mail do usuário",
        description=Users.email.comment,
    )


class UsersGetSchema(UsersInputSchema):
    """Esquema usado para responder a consultas à API sobre usuários, por
    meio do método HTTP GET.

    Campos ocultos não são mostrados.
    """

    model_config = ConfigDict(from_attributes=True)
    is_admin: bool = Field(
        title="se o usuário será administrador da api-pgd",
        default=False,
        description=Users.is_admin.comment,
    )
    disabled: bool = Field(
        title="se o usuário está ativo",
        default=False,
        description=Users.disabled.comment,
    )
    origem_unidade: OrigemUnidadeEnum = Field(
        title="Código do sistema da unidade (SIAPE ou SIORG)",
        description=Users.origem_unidade.comment,
    )
    cod_unidade_autorizadora: int = Field(
        title="Código da organização que autorizou o PGD",
        description=Users.cod_unidade_autorizadora.comment,
    )
    sistema_gerador: str = Field(
        title="sistema gerador dos dados",
        description=Users.sistema_gerador.comment,
    )


class UsersSchema(UsersGetSchema):
    password: str = Field(
        title="password encriptado",
        description=Users.password.comment,
    )

    @model_validator(mode="after")
    def validate_unidade(self):
        OrigemUnidadeValidation.must_be_valid_cod_unit(
            self.origem_unidade, self.cod_unidade_autorizadora
        )
        return self
