from typing import List, Optional
from pydantic import BaseModel


class PlanoTrabalho(BaseModel):
    id: int
    nome: str
    desc: Optional[str] = None
    qtde: Optional[float] = None
    # tags: List[str] = []
