from typing import List, Optional
from pydantic import BaseModel, Field
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
    qtde_entregas_efetivas: int
    avaliacao: int
    data_avaliacao: date
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
    data_interrupcao: date
    entregue_no_prazo: Optional[bool] = None #TODO Na especificação está como Int e usa 1 e 2 para sim e não. Não seria melhor usar bool?
    horas_homologadas: float

    atividades: List[AtividadeSchema] # = []

    class Config:
        orm_mode = True
        


