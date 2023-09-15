from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic import validator, root_validator # deprecated in 2.x
from datetime import date
from enum import IntEnum

from models import ModalidadesExecucao

class ContribuicoesSchema(BaseModel):
    tipo_contribuicao: int = Field(
        title="Tipo de contribuição",
        description="Tipos de contribuição\n"
            "\n"
            "* 1 - Vinculados a entregas da própria unidade;\n"
            "* 2 - Não vinculados diretamente a entregas da própria unidade,\n"
            "mas necessários ao adequado funcionamento administrativo ou à gestão de equipes e entregas;\n"
            "* 3 - Vinculados a entregas de outras unidades, órgãos ou entidades diversos\n"
    )
    descricao_contribuicao: Optional[str] = Field(
        title="Descrição da Contribuição",
    )
    id_entrega: Optional[int] = Field(
        title="Id da Entrega",
    )
    horas_vinculadas_entrega: int = Field(
        title="Horas vinculadas à entrega",
    )
class PlanoTrabalhoSchema(BaseModel):
    cod_SIAPE_instituidora: int = Field(
        title="Código SIAPE da organização que instituiu o PGD",
        description="Dado que virá do cadastro do usuário que envia o plano"
    )
    id_plano_trabalho_participante: int = Field(
        title="Id do Plano de Trabalho",
    )
    id_plano_entrega_unidade: int = Field(
        title="Id do Plano de Entregas da unidade"
    )
    cod_SIAPE_unidade_exercicio: int = Field(
        title="Código SIAPE da unidade de exercício do participante"
    )
    cpf_participante: int = Field(
        title="Número do CPF do participante",
        description="Sem pontos"
    )
    data_inicio_plano: date = Field(
        title="Data de início do plano"
    )
    data_termino_plano: date = Field(
        title="Data de término do plano"
    )
    carga_horaria_total_periodo_plano: int = Field(
        title="Carga horária total do período do plano de trabalho"
    )
    contribuicoes: Optional[List[ContribuicoesSchema]] = Field(
        title="Contribuições",
        description="Lista de Contribuições planejadas para o Plano de Trabalho"
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


    # @validator("cpf")
    # def cpf_validate(input_cpf):
    #     if not input_cpf.isdigit():
    #         raise ValueError("CPF deve conter apenas digitos.")

    #     cpf = [int(char) for char in input_cpf if char.isdigit()]
    #     #  Verifica se o CPF tem 11 dígitos
    #     if len(cpf) != 11:
    #         raise ValueError("CPF precisa ter 11 digitos.")

    #     #  Verifica se o CPF tem todos os números iguais, ex: 111.111.111-11
    #     #  Esses CPFs são considerados inválidos mas passam na validação dos dígitos
    #     if len(set(cpf)) == 1:
    #         raise ValueError("CPF inválido.")

    #     #  Valida os dois dígitos verificadores
    #     for i in range(9, 11):
    #         value = sum((cpf[num] * ((i+1) - num) for num in range(0, i)))
    #         digit = ((value * 10) % 11) % 10
    #         if digit != cpf[i]:
    #             raise ValueError("Digitos verificadores do CPF inválidos.")

    #     str_cpf = "".join([str(i) for i in input_cpf])
    #     return str_cpf

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

    class Config:
        orm_mode = True
