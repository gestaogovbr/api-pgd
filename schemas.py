from typing import List, Optional
from pydantic import BaseModel
from datetime import date

class Atividade(BaseModel):
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

class PlanoTrabalho(BaseModel):
    cod_unidade: int
    cod_plano_trabalho: str
    atividades: List[Atividade]
    matricula_siape: int
    cpf: str
    nome_participante: str
    cod_unidade_exercicio: int
    nome_unidade_exercicio: str
    local_execucao: int
    carga_horaria_semanal: int
    data_inicio: date
    data_fim: date
    carga_horaria_total: float
    data_interrupcao: date
    entregue_no_prazo: Optional[bool] = None #TODO Na especificação está como Int e usa 1 e 2 para sim e não. Não seria melhor usar bool?
    horas_homologadas: float
