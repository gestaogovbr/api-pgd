"""
Testes automáticos da API
"""
import os
import json
from types import GeneratorType as Generator
import requests

from fastapi.testclient import TestClient
from api import app
import pytest

# Fixtures

@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c

@pytest.fixture()
def input_pt():
    pt_json = {
  "cod_plano": "555",
  "matricula_siape": 0,
  "cpf": "99160773120",
  "nome_participante": "string",
  "cod_unidade_exercicio": 0,
  "nome_unidade_exercicio": "string",
  "modalidade_execucao": 1,
  "carga_horaria_semanal": 0,
  "data_inicio": "2021-01-07",
  "data_fim": "2021-01-12",
  "carga_horaria_total": 0,
  "data_interrupcao": "2021-01-07",
  "entregue_no_prazo": True,
  "horas_homologadas": 0,
  "atividades": [
    {
      "id_atividade": 2,
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
      "data_avaliacao": "2021-01-15",
      "justificativa": "string"
    },
    {
      "id_atividade": 3,
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
      "data_avaliacao": "2021-01-15",
      "justificativa": "string"
    }
  ]
}
    return pt_json

@pytest.fixture(scope="module")
def truncate_planos_trabalho(client):
    client.post(f"/truncate_pts_atividades")

@pytest.fixture(scope="module")
def truncate_users(client):
    client.post(f"/truncate_users")

def register_user(client, email, password, cod_unidade):
    data = {
        "email":email,
        "password":password,
        "cod_unidade": cod_unidade,
    }
    return client.post(f"/auth/register", data=json.dumps(data))


@pytest.fixture(scope="module")
def register_user_1(client, truncate_users):
    return register_user(client, "test1@api.com", "api", 1)

@pytest.fixture(scope="module")
def register_user_2(client, truncate_users):
    return register_user(client, "test2@api.com", "api", 2)

@pytest.fixture(scope="module")
def authed_header_user_1(register_user_1):
    """Authenticate in the API and return a dict with bearer header
    parameter to be passed to apis requests."""
    #TODO: Refatorar e resolver utilizando o objeto TestClient
    # data = {
    #     'grant_type': '',
    #     'username': 'nitai@example.com',
    #     'password': 'string',
    #     'scope': '',
    #     'client_id': '',
    #     'client_secret': ''
    # }
    # response = client.post(f"/auth/jwt/login", data=data)
    # print(response)
    # return response.json().get("access_token")

    # shell_cmd = 'curl -X POST "http://192.168.0.206:5057/auth/jwt/login"' \
    #                 ' -H  "accept: application/json"' \
    #                 ' -H  "Content-Type: application/json"' \
    #                 ' -d "grant_type=&username=test1%40api.com&password=api&scope=&client_id=&client_secret="'
    # my_cmd = os.popen(shell_cmd).read()
    # response = json.loads(my_cmd)
    # token_user_1 = response.get('access_token')
    
    url = "http://localhost:5057/auth/jwt/login"

    payload='accept=application%2Fjson&Content-Type=application%2Fjson&username=test1%40api.com&password=api'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)
    token_user_1 = response_dict.get('access_token')
    print(token_user_1)
    
    header = {
        'Authorization': f'Bearer {token_user_1}',
        'accept': 'application/json',
        'Content-Type': 'application/json'
        }

    return header
@pytest.fixture(scope="module")
def authed_header_user_2(register_user_2):
    """Authenticate in the API and return a dict with bearer header
    parameter to be passed to apis requests."""

    url = "http://localhost:5057/auth/jwt/login"

    payload='accept=application%2Fjson&Content-Type=application%2Fjson&username=test2%40api.com&password=api'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)
    token_user_1 = response_dict.get('access_token')
    print(token_user_1)
    
    header = {
        'Authorization': f'Bearer {token_user_1}',
        'accept': 'application/json',
        'Content-Type': 'application/json'
        }

    return header

# @pytest.fixture(scope="module")
# def insert_pt_user_1(authed_header_user_1, client):
#     client.put(f"/plano_trabalho/888888888",
#                json=input_pt,
#                headers=authed_header_user_1)

# Tests
def test_register_user(truncate_users, client):
    user_1 = register_user(client, "testx@api.com", "api", 0)
    assert user_1.status_code == 201

    user_2 = register_user(client, "testx@api.com", "api", 0)
    assert user_2.status_code == 400
    assert user_2.json().get("detail", None) == "REGISTER_USER_ALREADY_EXISTS"

def test_authenticate(authed_header_user_1):
    token = authed_header_user_1.get("Authorization")
    assert type(token) is str
    assert "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9." in token

def test_create_plano_trabalho(input_pt,
                               authed_header_user_1,
                               truncate_planos_trabalho,
                               client):
    response = client.put(f"/plano_trabalho/555",
                          data=json.dumps(input_pt),
                          headers=authed_header_user_1)
    assert response.status_code == 200
    assert response.json().get("detail", None) == None
    assert response.json() == input_pt

def test_create_pt_cod_plano_inconsistent(input_pt,
                                          authed_header_user_1,
                                          truncate_planos_trabalho,
                                          client):
    input_pt["cod_plano"] = 110
    response = client.put("/plano_trabalho/111",
                          json=input_pt,
                          headers=authed_header_user_1)
    assert response.status_code == 400
    detail_msg = "Parâmetro cod_plano diferente do conteúdo do JSON"
    assert response.json().get("detail", None) == detail_msg

# def test_get_plano_trabalho(insert_one_pt, authed_header_user_1):
def test_get_plano_trabalho(authed_header_user_1, client):
    response = client.get("/plano_trabalho/555",
                          headers=authed_header_user_1)
    assert response.status_code == 200

def test_get_pt_inexistente(authed_header_user_1, client):
    response = client.get("/plano_trabalho/888888888",
                          headers=authed_header_user_1)
    assert response.status_code == 404

    assert response.json().get("detail", None) == "Plano de trabalho não encontrado"

@pytest.mark.parametrize("data_inicio, data_fim, cod_plano, id_ati_1, id_ati_2",
                          [
                            ("2020-06-04", "2020-04-01", 77, 333, 334),
                            ("2020-06-04", "2020-04-01", 78, 335, 336),
                            ("2020-06-04", "2020-04-01", 79, 337, 338),
                            ])
def test_create_pt_invalid_dates(input_pt,
                                 data_inicio,
                                 data_fim,
                                 cod_plano,
                                 id_ati_1,
                                 id_ati_2,
                                 authed_header_user_1,
                                 truncate_planos_trabalho,
                                 client):
    input_pt['data_inicio'] = data_inicio
    input_pt['data_fim'] = data_fim
    input_pt['cod_plano'] = cod_plano
    input_pt['atividades'][0]['id_atividade'] = id_ati_1
    input_pt['atividades'][1]['id_atividade'] = id_ati_2

    response = client.put(f"/plano_trabalho/{cod_plano}",
                          json=input_pt,
                          headers=authed_header_user_1)
    if data_inicio > data_fim:
        assert response.status_code == 422
        detail_msg = "Data fim do Plano de Trabalho deve ser maior" \
                     " ou igual que Data início."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == 200

@pytest.mark.parametrize(
    "data_fim, data_avaliacao_1, data_avaliacao_2, cod_plano, id_ati_1, id_ati_2",
    [
      ("2020-06-04", "2020-04-01", "2020-04-01", 77, 333, 334),
      ("2020-06-04", "2020-04-01", "2021-04-01", 78, 335, 336),
      ("2020-06-04", "2020-04-01", "2019-04-01", 79, 337, 338),
      ("2020-04-01", "2020-04-01", "2020-06-04", 80, 339, 340),
      ("2020-04-01", "2020-04-01", "2020-04-01", 81, 341, 342),
      ("2020-04-01", "2020-02-01", "2020-01-04", 82, 343, 344),
      ])
def test_create_pt_invalid_data_avaliacao(input_pt,
                                          data_fim,
                                          data_avaliacao_1,
                                          data_avaliacao_2,
                                          cod_plano,
                                          id_ati_1,
                                          id_ati_2,
                                          authed_header_user_1,
                                          truncate_planos_trabalho,
                                          client):
    input_pt['data_inicio'] = "2020-01-01"
    input_pt['data_fim'] = data_fim
    input_pt['cod_plano'] = cod_plano
    input_pt['atividades'][0]['id_atividade'] = id_ati_1
    input_pt['atividades'][0]['data_avaliacao'] = data_avaliacao_1
    input_pt['atividades'][1]['id_atividade'] = id_ati_2
    input_pt['atividades'][1]['data_avaliacao'] = data_avaliacao_2

    response = client.put(f"/plano_trabalho/{cod_plano}",
                          json=input_pt,
                          headers=authed_header_user_1)
    if data_fim > data_avaliacao_1 or data_fim > data_avaliacao_2:
        assert response.status_code == 422
        detail_msg = "Data de avaliação da atividade deve ser maior ou igual" \
                     " que a Data Fim do Plano de Trabalho."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == 200

@pytest.mark.parametrize("cod_plano, id_ati_1, id_ati_2",
                          [
                            (90, 401, 402),
                            (91, 403, 403), # <<<< IGUAIS
                            (92, 404, 404), # <<<< IGUAIS
                            (93, 405, 406),
                            ])
def test_create_pt_duplicate_atividade(input_pt,
                                       cod_plano,
                                       id_ati_1,
                                       id_ati_2,
                                       authed_header_user_1,
                                       truncate_planos_trabalho,
                                       client):
    input_pt['cod_plano'] = cod_plano
    input_pt['atividades'][0]['id_atividade'] = id_ati_1
    input_pt['atividades'][1]['id_atividade'] = id_ati_2

    response = client.put(f"/plano_trabalho/{cod_plano}",
                          json=input_pt,
                          headers=authed_header_user_1)
    if id_ati_1 == id_ati_2:
        assert response.status_code == 400
        detail_msg = "Atividades devem possuir id_atividade diferentes."
        assert response.json().get("detail", None) == detail_msg
    else:
        assert response.status_code == 200

def test_update_pt_different_cod_unidade(input_pt,
                                         authed_header_user_2,
                                         client):
    cod_plano = 555
    response = client.put(f"/plano_trabalho/{cod_plano}",
                          json=input_pt,
                          headers=authed_header_user_2)

    assert response.status_code == 403
    detail_msg = "Usuário não pode alterar Plano de Trabalho de outra unidade."
    assert response.json().get("detail", None) == detail_msg

@pytest.mark.parametrize("cod_plano, cpf",
                          [
                            (100, '11111111111'),
                            (101, '22222222222'),
                            (102, '33333333333'),
                            (103, '44444444444'),                          
                            # (103, '444-444-444.44'),                          
                            # (103, '444.444.444-44'),                          
                            ])
def test_create_pt_invalid_cpf(input_pt,
                               cod_plano,
                               cpf,
                               authed_header_user_1,
                               truncate_planos_trabalho,
                               client):
    input_pt['cod_plano'] = cod_plano
    input_pt['cpf'] = cpf

    response = client.put(f"/plano_trabalho/{cod_plano}",
                          json=input_pt,
                          headers=authed_header_user_1)
    assert response.status_code == 422
    detail_msg = "CPF inválido"
    assert response.json().get("detail")[0]["msg"] == detail_msg

    
@pytest.mark.parametrize("cod_plano, modalidade_execucao",
                          [
                            (556, -1),
                            (81, -2),
                            (82, -3)                                                      
                            ])
def test_create_pt_invalid_modalidade_execucao(input_pt, 
                               cod_plano,                                              
                               modalidade_execucao,
                               authed_header_user_1,
                               truncate_planos_trabalho,
                               client):  
    input_pt['cod_plano'] = cod_plano
    input_pt['modalidade_execucao']= modalidade_execucao
    # print(input_pt)
    response = client.put(f"/plano_trabalho/{cod_plano}",
                          json=input_pt,
                          headers=authed_header_user_1)
    # print(response)
 
    assert response.status_code == 422
    detail_msg = "value is not a valid enumeration member; permitted: 1, 2, 3"
    assert response.json().get("detail")[0]["msg"] == detail_msg
