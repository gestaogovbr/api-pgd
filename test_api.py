"""
Testes automáticos
"""

from fastapi.testclient import TestClient
from api import app
import pytest

client =TestClient(app)

@pytest.fixture
def input_pt():
    pt_json = {
      "cod_plano": "555",
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
          "id_atividade": 909290,
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
          "id_atividade": 700290,
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
    return pt_json

@pytest.fixture(scope="module")
def truncate_bd():
    client.post(f"/truncate_pts_atividades")

def test_create_pt(truncate_bd, input_pt):
    response = client.put(f"/plano_trabalho/555", json=input_pt)
    assert response.status_code == 200
    assert response.json() == input_pt


def test_create_pt_cod_plano_inconsistent(truncate_bd, input_pt):
    input_pt["cod_plano"] = 110
    response = client.put("/plano_trabalho/111", json=input_pt)
    assert response.status_code == 400
    assert response.json().get("detail", None) == "Parâmetro cod_plano diferente do conteúdo do JSON"

def test_get_pt_inexistente():
    response = client.get("/plano_trabalho/888888888")
    assert response.status_code == 404
    assert response.json().get("detail", None) == "Plano de trabalho não encontrado"

@pytest.mark.parametrize("data_inicio, data_fim, cod_plano, id_ati_1, id_ati_2",
                          [
                            ("2020-06-04", "2020-04-01", 77, 333, 334),
                            ("2020-06-04", "2020-04-01", 78, 335, 336),
                            ("2020-06-04", "2020-04-01", 79, 337, 338),
                            ("2020-04-01", "2020-06-04", 80, 339, 340),
                            ])
def test_create_pt_invalid_dates(truncate_bd,
                                 input_pt,
                                 data_inicio,
                                 data_fim,
                                 cod_plano,
                                 id_ati_1,
                                 id_ati_2):
    input_pt['data_inicio'] = data_inicio
    input_pt['data_fim'] = data_fim
    input_pt['cod_plano'] = cod_plano
    input_pt['atividades'][0]['id_atividade'] = id_ati_1
    input_pt['atividades'][1]['id_atividade'] = id_ati_2

    response = client.put(f"/plano_trabalho/{cod_plano}", json=input_pt)
    if data_inicio > data_fim:
        assert response.status_code == 400
        assert response.json().get("detail", None) == "Data fim do Plano de Trabalho deve ser maior ou igual que Data início."
    else:
        assert response.status_code == 200
        # assert response.json() == input_pt # Para comparar estes objetos é preciso aceitar, por exemplo 0 = 0.0 nas propriedades do json

@pytest.mark.parametrize(
    "data_fim, data_avaliacao_1, data_avaliacao_2, cod_plano, id_ati_1, id_ati_2",
    [
      ("2020-06-04", "2020-04-01", "2020-04-01", 77, 333, 334),
      ("2020-06-04", "2020-04-01", "2021-04-01", 78, 335, 336),
      ("2020-06-04", "2020-10-01", "2019-04-01", 79, 337, 338),
      ("2020-04-01", "2020-04-01", "2020-06-04", 80, 339, 340),
      ("2020-04-01", "2020-04-01", "2020-04-01", 81, 341, 342),
      ("2020-04-01", "2020-02-01", "2020-01-04", 82, 343, 344),
      ])
def test_create_pt_invalid_data_avaliacao(truncate_bd,
                                          input_pt,
                                          data_fim,
                                          data_avaliacao_1,
                                          data_avaliacao_2,
                                          cod_plano,
                                          id_ati_1,
                                          id_ati_2):
    input_pt['data_inicio'] = "2020-01-01"
    input_pt['data_fim'] = data_fim
    input_pt['cod_plano'] = cod_plano
    input_pt['atividades'][0]['id_atividade'] = id_ati_1
    input_pt['atividades'][0]['data_avaliacao'] = data_avaliacao_1
    input_pt['atividades'][1]['id_atividade'] = id_ati_2
    input_pt['atividades'][1]['data_avaliacao'] = data_avaliacao_2

    response = client.put(f"/plano_trabalho/{cod_plano}", json=input_pt)
    if data_fim > data_avaliacao_1 or data_fim > data_avaliacao_2:
        assert response.status_code == 400
        assert response.json().get("detail", None) == "Data de avaliação da atividade deve maior ou igual que a Data Fim do Plano de Trabalho."
    else:
        assert response.status_code == 200
        # assert response.json() == input_pt # Para comparar estes objetos é preciso aceitar, por exemplo 0 = 0.0 nas propriedades do json

# @pytest.mark.parametrize("cod_plano, id_ati_1, id_ati_2",
#                           [
#                             (77, 333, 334),
#                             ])
# def test_create_pt_duplicate_atividade(truncate_bd,
#                                  input_pt,
#                                  data_inicio,
#                                  data_fim,
#                                  cod_plano,
#                                  id_ati_1,
#                                  id_ati_2):
#     input_pt['data_inicio'] = data_inicio
#     input_pt['data_fim'] = data_fim
#     input_pt['cod_plano'] = cod_plano
#     input_pt['atividades'][0]['id_atividade'] = id_ati_1
#     input_pt['atividades'][1]['id_atividade'] = id_ati_2

#     response = client.put(f"/plano_trabalho/{cod_plano}", json=input_pt)
#     if data_inicio > data_fim:
#         assert response.status_code == 400
#         assert response.json().get("detail", None) == "Data fim do Plano de Trabalho deve ser maior ou igual que Data início."
