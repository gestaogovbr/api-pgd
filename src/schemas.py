"""Módulo que define os esquemas de validação dos dados recebidos pela
API.

A principal ferramenta de validação de dados usada no FastAPI é o
Pydantic: https://docs.pydantic.dev/2.0/
"""

from datetime import date
from textwrap import dedent
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr
from pydantic import model_validator, field_validator

from models import (
    PlanoEntregas,
    Entrega,
    TipoMeta,
    lanoTrabalho,
    Contribuicao,
    AvaliacaoRegistrosExecucao,
    Participante,
    Users,
)
from util import over_a_year


# Função para validar CPF
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
    if not input_cpf.isdigit():
        raise ValueError("CPF deve conter apenas dígitos.")

    cpf = [int(char) for char in input_cpf if char.isdigit()]
    #  Verifica se o CPF tem 11 dígitos
    if len(cpf) != 11:
        raise ValueError("CPF precisa ter 11 dígitos.")

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


class ContribuicaoSchema(BaseModel):
    __doc__ = Contribuicao.__doc__
    model_config = ConfigDict(from_attributes=True)
    tipo_contribuicao: int = Field(
        title="Tipo de contribuição", description=Contribuicao.tipo_contribuicao.comment
    )
    descricao_contribuicao: Optional[str] = Field(
        default=None,
        title="Descrição da Contribuição",
        max_length=300,
        # description=Contribuicao.descricao_contribuicao.comment,
    )
    id_entrega: Optional[int] = Field(
        default=None, title="Id da Entrega", description=Contribuicao.id_entrega.comment
    )
    horas_vinculadas: int = Field(
        title="Horas vinculadas à determinada entrega",
        # description=Contribuicao.horas_vinculadas.comment,
    )

    @model_validator(mode="after")
    def must_be_mandatory_if(self) -> "ContribuicaoSchema":
        if self.tipo_contribuicao == 1 and self.id_entrega is None:
            raise ValueError(
                "O campo id_entrega é obrigatório quando tipo_contribuicao "
                "tiver o valor 1."
            )
        if self.tipo_contribuicao == 2 and self.id_entrega is not None:
            raise ValueError(
                "Não se deve informar id_entrega quando tipo_contribuicao == 2"
            )

        return self

    @field_validator("tipo_contribuicao")
    @staticmethod
    def must_be_between(tipo_contribuicao: int) -> int:
        if tipo_contribuicao not in range(1, 4):
            raise ValueError("Tipo de contribuição inválida; permitido: 1 a 3")
        return tipo_contribuicao

    @field_validator("horas_vinculadas")
    @staticmethod
    def must_be_zero_or_positive(horas_vinculadas: int) -> int:
        if horas_vinculadas < 0:
            raise ValueError("Valor de horas_vinculadas deve ser maior ou igual a zero")
        return horas_vinculadas


class ConsolidacaoSchema(BaseModel):
    __doc__ = Consolidacao.__doc__
    model_config = ConfigDict(from_attributes=True)
    data_inicio_registro: date = Field(
        title="Data de início do registro",
        description=Consolidacao.data_inicio_registro.comment,
    )
    data_fim_registro: date = Field(
        title="Data de fim do registro",
        description=Consolidacao.data_fim_registro.comment,
    )
    avaliacao_plano_trabalho: Optional[int] = Field(
        default=None,
        title="Avaliação do plano de trabalho",
        description=Consolidacao.avaliacao_plano_trabalho.comment,
    )

    @field_validator("avaliacao_plano_trabalho")
    @staticmethod
    def must_be_between(avaliacao_plano_trabalho: int) -> int:
        if (
            avaliacao_plano_trabalho is not None
            and avaliacao_plano_trabalho not in range(1, 6)
        ):
            raise ValueError(
                "Avaliação de plano de trabalho inválida; permitido: 1 a 5"
            )
        return avaliacao_plano_trabalho


class PlanoTrabalhoSchema(BaseModel):
    __doc__ = PlanoTrabalho.__doc__
    model_config = ConfigDict(from_attributes=True)
    cod_SIAPE_instituidora: int = Field(
        title="Código SIAPE da organização que instituiu o PGD",
        description=PlanoTrabalho.cod_SIAPE_instituidora.comment,
    )
    id_plano_trabalho_participante: int = Field(
        title="Id do Plano de Trabalho",
        description=PlanoTrabalho.id_plano_trabalho_participante.comment,
    )
    id_plano_entrega_unidade: int = Field(
        title="Id do Plano de Entregas da unidade",
        description=PlanoTrabalho.id_plano_entrega_unidade.comment,
    )
    cancelado: Optional[bool] = Field(
        default=False,
        title="Plano cancelado",
        description=PlanoTrabalho.cancelado.comment,
    )
    cod_SIAPE_unidade_exercicio: int = Field(
        title="Código SIAPE da unidade de exercício do participante",
        description=PlanoTrabalho.id_plano_entrega_unidade.comment,
    )
    cpf_participante: str = Field(
        title="Número do CPF do participante",
        description=PlanoTrabalho.cpf_participante.comment,
    )
    data_inicio_plano: date = Field(
        title="Data de início do plano",
        description=PlanoTrabalho.data_inicio_plano.comment,
    )
    data_termino_plano: date = Field(
        title="Data de término do plano",
        description=PlanoTrabalho.data_termino_plano.comment,
    )
    carga_horaria_total_periodo_plano: int = Field(
        title="Carga horária total do período do plano de trabalho",
        description=PlanoTrabalho.carga_horaria_total_periodo_plano.comment,
    )
    contribuicoes: Optional[List[ContribuicaoSchema]] = Field(
        default=None,
        title="Contribuições",
        description="Lista de Contribuições planejadas para o Plano de Trabalho.",
    )
    consolidacoes: Optional[List[ConsolidacaoSchema]] = Field(
        default=None,
        title="Consolidações",
        description="Lista de Consolidações (registros) de execução do Plano de Trabalho.",
    )

    @field_validator("cpf_participante")
    @staticmethod
    def cpf_part_validate(cpf_participante: str) -> str:
        return cpf_validate(cpf_participante)

    @model_validator(mode="after")
    def year_interval(self):
        if over_a_year(self.data_termino_plano, self.data_inicio_plano) == 1:
            raise ValueError(
                "Plano de trabalho não pode abranger período maior que 1 ano."
            )
        return self

    @model_validator(mode="after")
    def must_be_sequencial_dates(self):
        if self.data_inicio_plano > self.data_termino_plano:
            raise ValueError(
                "Data fim do Plano de Trabalho deve ser maior "
                "ou igual que Data de início."
            )
        return self

    @model_validator(mode="after")
    def consolidacao_must_be_in_period(self):
        if self.consolidacoes is not None and any(
            (consolidacao.data_inicio_registro < self.data_inicio_plano)
            or (consolidacao.data_fim_registro > self.data_termino_plano)
            for consolidacao in self.consolidacoes
        ):
            raise ValueError(
                "Data de início e de fim de registro devem estar contidos "
                "no período do Plano de Trabalho."
            )
        return self

    @model_validator(mode="after")
    def consolidacao_must_not_overlap(self):
        if self.consolidacoes is None:
            return self
        consolidacoes = sorted(
            self.consolidacoes,
            key=lambda consolidacao: consolidacao.data_inicio_registro,
        )
        # parear de 2 a 2
        for consolidacao1, consolidacao2 in zip(consolidacoes[:-1], consolidacoes[1:]):
            if (
                consolidacao1.data_inicio_registro < consolidacao2.data_fim_registro
                and consolidacao1.data_fim_registro > consolidacao2.data_inicio_registro
            ):
                raise ValueError(
                    "Uma ou mais consolidações possuem "
                    "data_inicio_registro e data_fim_registro sobrepostas."
                )
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
        max_length=300,
        description=Entrega.nome_entrega.comment,
    )
    meta_entrega: int = Field(
        title="Meta estipulada na inclusão no plano",
        description=Entrega.meta_entrega.comment,
    )
    tipo_meta: int = Field(
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
    )
    nome_unidade_destinataria: str = Field(
        title="Nome da unidade destinatária",
        description=Entrega.nome_unidade_destinataria.comment,
    )
    data_atualizacao: Optional[date] = Field(
        title="Data de atualização",
        description=Entrega.data_atualizacao.comment,
    )
    data_insercao: date = Field(
        title="Data de inserção",
        description=Entrega.data_insercao.comment,
    )

    @field_validator("tipo_meta")
    @staticmethod
    def must_be_in(tipo_meta: int) -> int:
        if tipo_meta not in (TipoMeta.unidade.value, TipoMeta.percentual.value):
            raise ValueError("Tipo de meta inválido; permitido: 1, 2")
        return tipo_meta

    @field_validator("meta_entrega")
    @staticmethod
    def must_be_positive(meta_entrega: int) -> int:
        if meta_entrega < 0:
            raise ValueError("Meta de entrega deve ser um valor positivo")
        return meta_entrega

    @field_validator("meta_entrega", mode="before")
    def validate_meta_percentual(self, meta_entrega: int) -> int:
        if (
            meta_entrega is not None
            and isinstance(meta_entrega, int)
            and self.tipo_meta == TipoMeta.percentual.value
            and not 0 <= meta_entrega <= 100
        ):
            raise ValueError("Meta percentual deve estar entre 0 e 100")
        return meta_entrega


class PlanoEntregasSchema(BaseModel):
    __doc__ = PlanoEntregas.__doc__
    model_config = ConfigDict(from_attributes=True)
    cod_SIAPE_instituidora: int = Field(
        title="Código SIAPE da organização que instituiu o PGD",
        description=PlanoEntregas.cod_SIAPE_instituidora.comment,
    )
    id_plano_entrega_unidade: int = Field(
        title="Id do plano de entregas da unidade",
        description=PlanoEntregas.id_plano_entrega_unidade.comment,
    )
    status: int = Field(
        title="Status do plano de entregas",
        description=PlanoEntregas.status.comment,
    )
    data_inicio_plano_entregas: date = Field(
        title="Data de início do plano de entregas",
        description=PlanoEntregas.data_inicio_plano_entregas.comment,
    )
    data_termino_plano_entregas: date = Field(
        title="Data de término do plano de entregas",
        description=PlanoEntregas.data_termino_plano_entregas.comment,
    )
    avaliacao_plano_entregas: Optional[int] = Field(
        default=None,
        title="Avaliação do plano de entregas",
        description=PlanoEntregas.avaliacao_plano_entregas.comment,
    )
    data_avaliacao_plano_entregas: Optional[date] = Field(
        default=None,
        title="Data de avaliação do plano de entregas",
        description=PlanoEntregas.data_avaliacao_plano_entregas.comment,
    )
    cod_SIAPE_unidade_plano: int = Field(
        title="Código SIAPE da unidade do plano de entregas",
        description=PlanoEntregas.cod_SIAPE_unidade_plano.comment,
    )
    entregas: List[EntregaSchema] = Field(
        title="Entregas",
        description="Lista de entregas associadas ao Plano de Entregas",
    )

    @field_validator("status")
    def validate_status(self, v):
        if v not in range(1, 6):
            raise ValueError("Status inválido; permitido: 1, 2, 3, 4, 5")
        if v == 5 and (
            self.avaliacao_plano_entregas is None
            or self.data_avaliacao_plano_entregas is None
        ):
            raise ValueError(
                "Status 5 (Avaliado) requer avaliacao_plano_entregas e "
                "data_avaliacao_plano_entregas preenchidos"
            )
        return v

    @field_validator("cod_SIAPE_instituidora", "cod_SIAPE_unidade_plano")
    def validate_cod_SIAPE(self, v):
        if v < 1:
            raise ValueError("cod_SIAPE inválido")
        return v

    @field_validator("data_termino_plano_entregas")
    def validate_data_termino(self, v, values):
        if v < values["data_inicio_plano_entregas"]:
            raise ValueError(
                "data_termino_plano_entregas deve ser maior ou igual que "
                "data_inicio_plano_entregas"
            )
        return v

    @field_validator("data_avaliacao_plano_entregas")
    def validate_data_avaliacao(self, v, values):
        if v is not None and v < values["data_inicio_plano_entregas"]:
            raise ValueError


class StatusParticipanteSchema(BaseModel):
    __doc__ = StatusParticipante.__doc__
    model_config = ConfigDict(from_attributes=True)
    cod_SIAPE_instituidora: int = Field(
        title="Código SIAPE da organização que instituiu o PGD",
        description=PlanoEntregas.cod_SIAPE_instituidora.comment,
    )
    cpf_participante: str = Field(
        title="Número do CPF do participante",
        description=StatusParticipante.cpf_participante.comment,
    )
    matricula_siape: Optional[str] = Field(
        default=None,
        title="Número da matrícula do participante",
        description=StatusParticipante.matricula_siape.comment,
    )
    participante_ativo_inativo_pgd: int = Field(
        title="Situação do participante no Programa de Gestão e Desempenho (PGD)",
        description=StatusParticipante.participante_ativo_inativo_pgd.comment,
    )
    modalidade_execucao: int = Field(
        title="Modalidade e regime de execução do trabalho do participante",
        description=StatusParticipante.modalidade_execucao.comment,
    )
    jornada_trabalho_semanal: int = Field(
        title="Jornada de trabalho semanal",
        description=StatusParticipante.jornada_trabalho_semanal.comment,
    )
    data_envio: date = Field(
        title="Timestamp do envio dos dados",
        description=StatusParticipante.data_envio.comment,
    )

    @field_validator("cpf_participante")
    @staticmethod
    def cpf_part_validate(cpf_participante: str) -> str:
        return cpf_validate(cpf_participante)

    @field_validator("matricula_siape")
    @staticmethod
    def siape_validate(matricula_siape: str) -> str:
        if matricula_siape is None:
            return matricula_siape
        if len(matricula_siape) != 7:
            raise ValueError("Matrícula SIAPE deve ter 7 dígitos.")
        if len(set(matricula_siape)) < 2:
            raise ValueError("Matricula SIAPE Inválida.")
        return matricula_siape

    @field_validator("participante_ativo_inativo_pgd")
    @staticmethod
    def must_be_bool(participante_ativo_inativo_pgd: int) -> int:
        """Verifica se o campo participante_ativo_inativo_pgd está
        entre os valores permitidos.

        Foi usado int em vez de bool para preservar a possibilidade
        futura de passar a aceitar um valor diferente.
        """
        if participante_ativo_inativo_pgd not in (0, 1):
            raise ValueError(
                "Valor do campo 'participante_ativo_inativo_pgd' inválida; "
                "permitido: 0, 1"
            )
        return participante_ativo_inativo_pgd

    @field_validator("modalidade_execucao")
    @staticmethod
    def must_be_between(modalidade_execucao: int) -> int:
        if modalidade_execucao not in range(1, 4):
            raise ValueError("Modalidade de execução inválida; permitido: 1, 2, 3, 4")
        return modalidade_execucao

    @field_validator("jornada_trabalho_semanal")
    @staticmethod
    def must_be_positive(jornada_trabalho_semanal: int) -> int:
        if jornada_trabalho_semanal < 1:
            raise ValueError("Jornada de trabalho semanal deve ser maior que zero")
        return jornada_trabalho_semanal


class ListaStatusParticipanteSchema(BaseModel):
    """Lista de status do participante."""

    model_config = ConfigDict(from_attributes=True)
    lista_status: List[StatusParticipanteSchema] = Field(
        title="Contribuições",
        description="Lista de Contribuições planejadas para o Plano de Trabalho.",
    )


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UsersInputSchema(BaseModel):
    __doc__ = Users.__doc__
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr = Field(
        title="e-mail do usuário",
        description=Users.email.comment,
    )


class UsersGetSchema(UsersInputSchema):
    __doc__ = Users.__doc__
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
    cod_unidade_autorizadora: int = Field(
        title="Código SIAPE da organização que autorizou o PGD",
        description=Users.cod_unidade_autorizadora.comment,
    )


class UsersSchema(UsersGetSchema):
    password: str = Field(
        title="password encriptado",
        description=Users.password.comment,
    )

    @field_validator("cod_unidade_autorizadora")
    @staticmethod
    def must_be_positive(cod_unidade: int) -> int:
        if cod_unidade < 1:
            raise ValueError("cod_SIAPE inválido")
        return cod_unidade
