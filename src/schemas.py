"""Módulo que define os esquemas de validação dos dados recebidos pela
API.

A principal ferramenta de validação de dados usada no FastAPI é o
Pydantic: https://docs.pydantic.dev/2.0/
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic import field_validator
from datetime import date
from enum import IntEnum

from models import PlanoEntregas, PlanoTrabalho, Entrega
from models import Consolidacao, Contribuicao, StatusParticipante


# Função para validar CPF
def cpf_validate(input_cpf):
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
    model_config = ConfigDict(from_attributes=True)
    tipo_contribuicao: int = Field(
        title="Tipo de contribuição", description=Contribuicao.tipo_contribuicao.comment
    )
    descricao_contribuicao: Optional[str] = Field(
        default=None,
        title="Descrição da Contribuição",
        description=Contribuicao.descricao_contribuicao.comment,
    )
    id_entrega: Optional[int] = Field(
        default=None, title="Id da Entrega", description=Contribuicao.id_entrega.comment
    )
    horas_vinculadas: int = Field(
        title="Horas vinculadas à determinada entrega",
        description=Contribuicao.horas_vinculadas.comment,
    )


class ConsolidacaoSchema(BaseModel):
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
        title="Avaliação do plano de trabalho",
        description=Consolidacao.avaliacao_plano_trabalho.comment,
    )


class PlanoTrabalhoSchema(BaseModel):
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
        title="Contribuições",
        description="Lista de Contribuições planejadas para o Plano de Trabalho.",
    )
    consolidacoes: Optional[List[ConsolidacaoSchema]] = Field(
        title="Consolidações",
        description="Lista de Consolidações (registros) de execução do Plano de Trabalho.",
    )

    # Validações
    # @root_validator
    # def data_validate(cls, values):
    #     data_inicio = values.get("data_inicio", None)
    #     data_fim = values.get("data_fim", None)
    #     if data_inicio > data_fim:
    #         raise ValueError("Data fim do Plano de Trabalho deve ser maior" \
    #                  " ou igual que Data de início.")
    #     for atividade in values.get("atividades", []):
    #         if getattr(atividade, "data_avaliacao", None) is not None and \
    #             atividade.data_avaliacao < data_inicio:
    #                 raise ValueError("Data de avaliação da atividade deve ser maior ou igual" \
    #                     " que a Data de início do Plano de Trabalho.")
    #     return values

    # @validator("atividades")
    # def valida_atividades(cls, atividades):
    #     ids_atividades = [a.id_atividade for a in atividades]
    #     duplicados = []
    #     for id_atividade in ids_atividades:
    #         if id_atividade not in duplicados:
    #             duplicados.append(id_atividade)
    #         else:
    #             raise ValueError("Atividades devem possuir id_atividade diferentes.")
    #     return atividades

    @field_validator("cpf_participante")
    def cpf_part_validate(cls, cpf_participante):
        return cpf_validate(cpf_participante)

    # @validator("carga_horaria_semanal")
    # def must_be_less(cls, carga_horaria_semanal):
    #     if carga_horaria_semanal > 40 or carga_horaria_semanal <= 0:
    #         raise ValueError("Carga horária semanal deve ser entre 1 e 40")
    #     return carga_horaria_semanal

    # @validator("horas_homologadas")
    # def must_be_positive(cls, horas_homologadas):
    #     if horas_homologadas <= 0:
    #         raise ValueError("Horas homologadas devem ser maior que zero")
    #     return horas_homologadas


class EntregaSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_entrega: int = Field(
        title="Id da entrega",
    )
    nome_entrega: str = Field(
        title="Nome da entrega", description=Entrega.nome_entrega.comment
    )
    meta_entrega: int = Field(
        title="Meta estipulada na inclusão no plano",
        description=Entrega.meta_entrega.comment,
    )
    tipo_meta: int = Field(title="Tipo da meta", description=Entrega.tipo_meta.comment)
    nome_vinculacao_cadeia_valor: Optional[str] = Field(
        title="Nome da vinculação de cadeia de valor",
        description=Entrega.nome_vinculacao_cadeia_valor.comment,
    )
    nome_vinculacao_planejamento: Optional[str] = Field(
        title="Nome da vinculação do planejamento",
        description=Entrega.nome_vinculacao_planejamento.comment,
    )
    percentual_progresso_esperado: Optional[int] = Field(
        title="Percentual de progresso esperado",
        description=Entrega.percentual_progresso_esperado.comment,
    )
    percentual_progresso_realizado: Optional[int] = Field(
        title="Percentual de progresso realizado",
        description=Entrega.percentual_progresso_realizado.comment,
    )
    data_entrega: Optional[date] = Field(
        title="Data da entrega", description=Entrega.data_entrega.comment
    )
    nome_demandante: Optional[str] = Field(
        title="Nome do demandante", description=Entrega.nome_demandante.comment
    )
    nome_destinatario: Optional[str] = Field(
        title="Nome do destinatário", description=Entrega.nome_destinatario.comment
    )


class PlanoEntregasSchema(BaseModel):
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
        title="Avaliação do plano de entregas",
        description=PlanoEntregas.avaliacao_plano_entregas.comment,
    )
    data_avaliacao_plano_entregas: Optional[date] = Field(
        title="Data de avaliação do plano de entregas",
        description=PlanoEntregas.data_avaliacao_plano_entregas.comment,
    )
    cod_SIAPE_unidade_plano: int = Field(
        title="Código SIAPE da unidade do plano de entregas",
        description=PlanoEntregas.cod_SIAPE_unidade_plano.comment,
    )
    entregas: Optional[List[EntregaSchema]] = Field(
        title="Entregas",
        description="Lista de entregas associadas ao Plano de Entregas",
    )


class StatusParticipanteSchema(BaseModel):
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
    def cpf_part_validate(cls, cpf_participante):
        return cpf_validate(cpf_participante)

    @field_validator("matricula_siape")
    def siape_validate(cls, matricula_siape):
        if len(matricula_siape) != 7:
            raise ValueError(
                "Matricula SIAPE Inválida.", "Matrícula SIAPE deve ter 7 dígitos."
            )
        return matricula_siape

    @field_validator("participante_ativo_inativo_pgd")
    def must_be_bool(cls, participante_ativo_inativo_pgd):
        if participante_ativo_inativo_pgd not in (0, 1):
            raise ValueError(
                "Valor do campo 'participante_ativo_inativo_pgd' inválida; "
                "permitido: 0, 1"
            )
        return participante_ativo_inativo_pgd

    @field_validator("modalidade_execucao")
    def must_be_between(cls, modalidade_execucao):
        if modalidade_execucao not in range(1, 4):
            raise ValueError("Modalidade de execução inválida; permitido: 1, 2, 3, 4")
        return modalidade_execucao

    @field_validator("jornada_trabalho_semanal")
    def must_be_positive(cls, jornada_trabalho_semanal):
        if jornada_trabalho_semanal < 1:
            raise ValueError("Jornada de trabalho semanal deve ser maior que zero")
        return jornada_trabalho_semanal
