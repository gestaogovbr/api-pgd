from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel

class Plano_Trabalho(BaseModel):
    id: int
    nome: str
    desc: Optional[str] = None
    qtde: Optional[float] = None
    # tags: List[str] = []

app = FastAPI()

@app.get('/hello')
def hello():
    """Test endpoint"""
    return {'hello': 'world'}

@app.post("/items/", response_model=Plano_Trabalho)
async def create_item(item: Plano_Trabalho):
    return item
