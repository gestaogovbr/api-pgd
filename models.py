"""Definições dos modelos de dados da API que serão persistidos no
banco pelo ORM do SQLAlchemy.
"""

from sqlalchemy import (Boolean, Column, ForeignKey,
                        Integer, String, Float, Date)
from sqlalchemy.orm import relationship

from database import Base

class PlanoTrabalho(Base):
    "Plano de Trabalho"
    __tablename__ = 'plano_trabalho'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cod_unidade = Column(Integer)
    cod_plano = Column(String)
    matricula_siape = Column(Integer)
    cpf = Column(String)
    nome_participante = Column(String)
    cod_unidade_exercicio = Column(Integer)
    nome_unidade_exercicio = Column(String)
    local_execucao = Column(Integer)
    carga_horaria_semanal = Column(Integer)
    data_inicio = Column(Date)
    data_fim = Column(Date)
    carga_horaria_total = Column(Float)
    data_interrupcao = Column(Date)
    entregue_no_prazo = Column(Boolean) #TODO Na especificação está como Int e usa 1 e 2 para sim e não. Não seria melhor usar bool?
    horas_homologadas = Column(Float)
    atividades = relationship('Atividade', backref='plano_trabalho')

class Atividade(Base):
    "Atividade"
    __tablename__ = 'atividade'
    id_atividade = Column(Integer, primary_key=True, index=True)
    id_plano_trabalho = Column(Integer, ForeignKey('plano_trabalho.id'))
    nome_grupo_atividade = Column(String)
    nome_atividade = Column(String)
    faixa_complexidade = Column(String)
    parametros_complexidade = Column(String)
    tempo_exec_presencial = Column(Float)
    tempo_exec_teletrabalho = Column(Float)
    entrega_esperada = Column(String)
    qtde_entregas = Column(Integer)
    qtde_entregas_efetivas = Column(Integer)
    avaliacao = Column(Integer)
    data_avaliacao = Column(Date)
    justificativa = Column(String)
