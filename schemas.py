from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError, validator, root_validator
from datetime import date
from enum import IntEnum

class AtividadeSchema(BaseModel):
    id_atividade: int
    nome_grupo_atividade: Optional[str]
    nome_atividade: str
    faixa_complexidade: str
    parametros_complexidade: Optional[str]
    tempo_exec_presencial: float
    tempo_exec_teletrabalho: float
    entrega_esperada: Optional[str]
    qtde_entregas: int
    qtde_entregas_efetivas: Optional[int]
    avaliacao: Optional[int]
    data_avaliacao: Optional[date]
    justificativa: Optional[str]

    class Config:
        orm_mode = True

class ModalidadeEnum(IntEnum):
    presencial = 1
    semipresencial = 2
    teletrabalho = 3

class PlanoTrabalhoSchema(BaseModel):
    cod_plano: str
    matricula_siape: int
    cpf: str
    nome_participante: str
    cod_unidade_exercicio: int
    nome_unidade_exercicio: str
    modalidade_execucao: ModalidadeEnum = Field(None, alias='modalidade_execucao')
    carga_horaria_semanal: int
    data_inicio: date
    data_fim: date
    carga_horaria_total: float
    data_interrupcao: Optional[date]
    entregue_no_prazo: Optional[bool] = None #TODO Na especificação está como Int e usa 1 e 2 para sim e não. Não seria melhor usar bool?
    horas_homologadas: Optional[float]
    atividades: List[AtividadeSchema] # = []

    # Validações
    @root_validator
    def data_validate(cls, values):
        data_inicio = values.get('data_inicio', None)
        data_fim = values.get('data_fim', None)
        atividades = values.get('atividades')[0]
        if data_inicio > data_fim:
            raise ValueError("Data fim do Plano de Trabalho deve ser maior" \
                     " ou igual que Data início.")
        if data_fim > atividades.data_avaliacao:
            raise ValueError("Data de avaliação da atividade deve ser maior ou igual" \
                     " que a Data Fim do Plano de Trabalho.")
        return values

    @root_validator
    def validate_carga_horaria_total(cls, values):
        total_sum = 0
        for a in values.get('atividades'):
            total_sum += (getattr(a, 'tempo_exec_presencial') +
                          getattr(a, 'tempo_exec_teletrabalho'))
        if total_sum != values.get('carga_horaria_total'):
            raise ValueError('A soma dos tempos de execução presencial e ' \
                             'teletrabalho das atividades deve ser igual à ' \
                             'carga_horaria_total.')
        return values

    @validator('atividades')
    def valida_atividades(cls, atividades):
        ids_atividades = [a.id_atividade for a in atividades]
        duplicados = []
        for id_atividade in ids_atividades:
            if id_atividade not in duplicados:
                duplicados.append(id_atividade)
            else:
                raise ValueError("Atividades devem possuir id_atividade diferentes.")
        return atividades


    @validator('cpf')
    def cpf_validate(input_cpf):
        if not input_cpf.isdigit():
            raise ValueError('CPF deve conter apenas digitos.')

        cpf = [int(char) for char in input_cpf if char.isdigit()]
        #  Verifica se o CPF tem 11 dígitos
        if len(cpf) != 11:
            raise ValueError('CPF precisa ter 11 digitos.')

        #  Verifica se o CPF tem todos os números iguais, ex: 111.111.111-11
        #  Esses CPFs são considerados inválidos mas passam na validação dos dígitos
        if len(set(cpf)) == 1:
            raise ValueError('CPF inválido.')

        #  Valida os dois dígitos verificadores
        for i in range(9, 11):
            value = sum((cpf[num] * ((i+1) - num) for num in range(0, i)))
            digit = ((value * 10) % 11) % 10
            if digit != cpf[i]:
                raise ValueError('Digitos verificadores do CPF inválidos.')

        str_cpf = ''.join([str(i) for i in input_cpf])
        return str_cpf

    @validator('carga_horaria_semanal')
    def must_be_less(cls, carga_horaria_semanal):
        if carga_horaria_semanal > 40 or carga_horaria_semanal <= 0:
            raise ValueError('Carga horária semanal deve ser entre 1 e 40')
        return carga_horaria_semanal

    class Config:
        orm_mode = True
