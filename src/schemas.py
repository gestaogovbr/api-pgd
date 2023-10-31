"""Módulo que define os esquemas de validação dos dados recebidos pela
API.

A principal ferramenta de validação de dados usada no FastAPI é o
Pydantic: https://docs.pydantic.dev/2.0/
"""

from typing import List, Optional
from datetime import date

from pydantic import BaseModel, ConfigDict, Field
from pydantic import model_validator, field_validator

from models import PlanoEntregas, PlanoTrabalho, Entrega
from models import Consolidacao, Contribuicao, StatusParticipante
from util import over_a_year


# Função para validar CPF
def cpf_validate(input_cpf: str) -> str:
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

    str_cpf = "".join([str(i) for i in input_cpf])
    return str_cpf


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
        description=Contribuicao.descricao_contribuicao.comment,
    )
    id_entrega: Optional[int] = Field(
        default=None, title="Id da Entrega", description=Contribuicao.id_entrega.comment
    )
    horas_vinculadas: int = Field(
        title="Horas vinculadas à determinada entrega",
        description=Contribuicao.horas_vinculadas.comment,
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
    id_entrega: int = Field(
        title="Id da entrega",
    )
    nome_entrega: str = Field(
        title="Nome da entrega",
        max_length=300,
        description=Entrega.nome_entrega.comment,
    )
    meta_entrega: int = Field(
        title="Meta estipulada na inclusão no plano",
        description=Entrega.meta_entrega.comment,
    )
    tipo_meta: int = Field(title="Tipo da meta", description=Entrega.tipo_meta.comment)
    nome_vinculacao_cadeia_valor: Optional[str] = Field(
        default=None,
        title="Nome da vinculação de cadeia de valor",
        max_length=300,
        description=Entrega.nome_vinculacao_cadeia_valor.comment,
    )
    nome_vinculacao_planejamento: Optional[str] = Field(
        default=None,
        max_length=300,
        title="Nome da vinculação do planejamento",
        description=Entrega.nome_vinculacao_planejamento.comment,
    )
    percentual_progresso_esperado: Optional[int] = Field(
        default=None,
        title="Percentual de progresso esperado",
        description=Entrega.percentual_progresso_esperado.comment,
    )
    percentual_progresso_realizado: Optional[int] = Field(
        default=None,
        title="Percentual de progresso realizado",
        description=Entrega.percentual_progresso_realizado.comment,
    )
    data_entrega: Optional[date] = Field(
        default=None, title="Data da entrega", description=Entrega.data_entrega.comment
    )
    nome_demandante: Optional[str] = Field(
        default=None,
        title="Nome do demandante",
        max_length=300,
        description=Entrega.nome_demandante.comment,
    )
    nome_destinatario: Optional[str] = Field(
        default=None,
        title="Nome do destinatário",
        max_length=300,
        description=Entrega.nome_destinatario.comment,
    )

    @field_validator("tipo_meta")
    @staticmethod
    def must_be_in(tipo_meta: int) -> int:
        if tipo_meta not in (1, 2):
            raise ValueError("Tipo de meta inválido; permitido: 1, 2")
        return tipo_meta

    @field_validator(
        "meta_entrega",
        "percentual_progresso_esperado",
        "percentual_progresso_realizado",
    )
    @staticmethod
    def must_be_percent(percent: int) -> int:
        if percent is not None and not 0 <= percent <= 100:
            raise ValueError("Valor percentual inválido.")
        return percent


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
    cancelado: Optional[bool] = Field(
        default=False,
        title="Plano cancelado",
        description=PlanoEntregas.cancelado.comment,
    )
    data_inicio_plano_entregas: date = Field(
        title="Data de início estipulada no plano de entregas",
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

    @field_validator("avaliacao_plano_entregas")
    @staticmethod
    def must_be_between(avaliacao_plano_entregas: int) -> int:
        if (
            avaliacao_plano_entregas is not None
            and avaliacao_plano_entregas not in range(1, 6)
        ):
            raise ValueError("Nota de avaliação inválida; permitido: 1, 2, 3, 4, 5")
        return avaliacao_plano_entregas

    @field_validator("cod_SIAPE_instituidora", "cod_SIAPE_unidade_plano")
    @staticmethod
    def must_be_positive(cod_unidade: int) -> int:
        if cod_unidade < 1:
            raise ValueError("cod_SIAPE inválido")
        return cod_unidade

    @model_validator(mode="after")
    def must_be_unique(self) -> "PlanoEntregasSchema":
        entregas_list = []
        for entrega in self.entregas:
            entregas_list.append(entrega.id_entrega)

        if any(entregas_list.count(x) > 1 for x in entregas_list):
            raise ValueError("Entregas devem possuir id_entrega diferentes")
        return self

    @model_validator(mode="after")
    def year_interval(self) -> "PlanoEntregasSchema":
        if (
            over_a_year(
                self.data_termino_plano_entregas, self.data_inicio_plano_entregas
            )
            == 1
        ):
            raise ValueError(
                "Plano de entregas não pode abranger período maior que 1 ano."
            )
        return self

    @model_validator(mode="after")
    def must_be_proper_period(self) -> "PlanoEntregasSchema":
        if self.data_termino_plano_entregas < self.data_inicio_plano_entregas:
            raise ValueError(
                "data_termino_plano_entregas deve ser maior ou igual que "
                "data_inicio_plano_entregas."
            )
        return self

    @model_validator(mode="after")
    def must_be_sequential_dates(self) -> "PlanoEntregasSchema":
        if (self.data_avaliacao_plano_entregas is not None) and (
            self.data_avaliacao_plano_entregas < self.data_inicio_plano_entregas
        ):
            raise ValueError(
                "Data de avaliação do Plano de Entrega deve ser maior ou igual"
                " que a Data de início do Plano de Entrega."
            )
        return self

    @model_validator(mode="after")
    def must_be_in_period(self) -> "PlanoEntregasSchema":
        if any(
            entrega.data_entrega < self.data_inicio_plano_entregas
            or entrega.data_entrega > self.data_termino_plano_entregas
            for entrega in self.entregas
        ):
            raise ValueError(
                "Data de entrega precisa estar dentro do intervalo entre "
                "início e término do Plano de Entregas."
            )
        return self


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
