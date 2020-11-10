"""Definições dos modelos de dados da API que serão persistidos no
banco pelo ORM do SQLAlchemy.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship

from database import Base

class PlanoTrabalho(Base):
    "Plano de Trabalho"
    __tablename__ = 'plano_trabalho'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    desc = Column(String)
    qtde = Column(Float)
