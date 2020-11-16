"""
Testes automáticos
"""

from fastapi.testclient import TestClient
from api import app

client =TestClient(app)

pt_json = {
  "cod_unidade": 0,
  "cod_plano": "9999",
  "matricula_siape": 0,
  "cpf": "string",
  "nome_participante": "string",
  "cod_unidade_exercicio": 0,
  "nome_unidade_exercicio": "string",
  "local_execucao": 0,
  "carga_horaria_semanal": 0,
  "data_inicio": "2020-11-14",
  "data_fim": "2020-11-14",
  "carga_horaria_total": 0,
  "data_interrupcao": "2020-11-14",
  "entregue_no_prazo": True,
  "horas_homologadas": 0,
  "atividades": [
    {
      "id_atividade": 90,
      "nome_grupo_atividade": "string",
      "nome_atividade": "string",
      "faixa_complexidade": "string",
      "parametros_complexidade": "string",
      "tempo_exec_presencial": 0,
      "tempo_exec_teletrabalho": 0,
      "entrega_esperada": "string",
      "qtde_entregas": 0,
      "qtde_entregas_efetivas": 0,
      "avaliacao": 0,
      "data_avaliacao": "2020-11-14",
      "justificativa": "string"
    },
    {
      "id_atividade": 70,
      "nome_grupo_atividade": "string",
      "nome_atividade": "string",
      "faixa_complexidade": "string",
      "parametros_complexidade": "string",
      "tempo_exec_presencial": 0,
      "tempo_exec_teletrabalho": 0,
      "entrega_esperada": "string",
      "qtde_entregas": 0,
      "qtde_entregas_efetivas": 0,
      "avaliacao": 0,
      "data_avaliacao": "2020-11-14",
      "justificativa": "string"
    }
  ]
}

def test_create_pt():
    response = client.put("/plano_trabalho/9999", json=pt_json)
    assert response.status_code == 200
    assert response.json() == pt_json

def test_create_pt_cod_plano_inconsistent():
    pt_json["cod_plano"] = 110
    response = client.put("/plano_trabalho/111", json=pt_json)
    assert response.status_code == 400
    assert response.json() == {"detail": "Parâmetro cod_plano diferente do conteúdo do JSON"}

def test_get_pt_inexistente():
    response = client.get("/plano_trabalho/888888888")
    assert response.status_code == 404
    assert response.json() == {"detail": "Plano de trabalho não encontrado"}