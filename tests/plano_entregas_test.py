"""
Testes relacionados ao Plano de Entregas da Unidade
"""
import itertools

from httpx import Client

from fastapi import status

import pytest

# grupos de campos opcionais e obrigatórios a testar

fields_plano_entregas = {
    "optional": (
        ["avaliacao_plano_entregas", "data_avaliacao_plano_entregas"],
        ["nome_vinculacao_cadeia_valor"],
        ["nome_vinculacao_planejamento"],
        ["percentual_progresso_esperado"],
        ["percentual_progresso_realizado"],
    ),
    "mandatory": (
        ["id_plano_entrega_unidade"],
        ["data_inicio_plano_entregas"],
        ["data_termino_plano_entregas"],
        ["cod_SIAPE_unidade_plano"],
        ["entregas"],
        ["id_entrega"],
        ["nome_entrega"],
        ["meta_entrega"],
        ["tipo_meta"],
        ["data_entrega"],
        ["nome_demandante"],
        ["nome_destinatario"]
    )
}

def test_create_plano_entregas_completo(input_pe: dict,
                                        header_usr_1: dict,
                                        truncate_pe,
                                        client: Client):
    """Tenta criar um novo plano de entregas"""
    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/555",
                          json=input_pe,
                          headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_pe

def test_update_plano_trabalho(input_pe: dict,
                               example_pe,
                               header_usr_1: dict,
                               truncate_pe,
                               client: Client):
    """Tenta criar um novo plano de entregas e atualizar alguns campos
    A fixture example_pe cria um novo Plano de Entrega na API
    Altera um campo do PE e reenvia pra API (update)
    TODO: Validar regra negocial - No update devem ser enviados as entregas novamente?
    """

    input_pe["avaliacao_plano_entregas"] = 3
    input_pe["data_avaliacao_plano_entregas"] = "2023-08-15"
    client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/555", json=input_pe, headers=header_usr_1)
    # Consulta API para conferir se a alteração foi persistida
    response = client.get(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/555", headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["avaliacao_plano_entregas"] == 3
    assert response.json()["data_avaliacao_plano_entregas"] == "2023-08-15"   

@pytest.mark.parametrize("omitted_fields",
                         enumerate(fields_plano_entregas["optional"]))
def test_create_plano_trabalho_omit_optional_fields(input_pe: dict,
                                             omitted_fields: list,
                                             header_usr_1: dict,
                                             truncate_pe,
                                             client: Client):
    """Tenta criar um novo plano de entregas omitindo campos opcionais"""

    offset, field_list = omitted_fields
    for field in field_list:
        del input_pe[field]

    input_pe["id_plano_entrega_unidade"] = 557 + offset
    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/{input_pe['id_plano_entrega_unidade']}",
                          json=input_pe,
                          headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.parametrize("missing_fields",
                         enumerate(fields_plano_entregas["mandatory"]))
def test_create_plano_entrega_missing_mandatory_fields(input_pe: dict,
                                             missing_fields: list,
                                             header_usr_1: dict,
                                             truncate_pe,
                                             client: Client):
    """Tenta criar um plano de entregas, faltando campos obrigatórios.
    Tem que ser um plano de entregas novo, pois na atualização de um
    plano de trabalho existente, o campo que ficar faltando será
    interpretado como um campo que não será atualizado, ainda que seja
    obrigatório para a criação.
    """
    offset, field_list = missing_fields
    for field in field_list:
        del input_pe[field]

    input_pe["id_plano_entrega_unidade"] = 1800 + offset # precisa ser um novo plano
    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/{input_pe['id_plano_entrega_unidade']}",
                          json=input_pe,
                          headers=header_usr_1)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_create_huge_plano_entrega(input_pe: dict,
                                    header_usr_1: dict,
                                    truncate_pe,
                                    client: Client):
    def create_huge_entrega(id_entrega: str):
        new_entrega = input_pe["entregas"][0].copy()
        new_entrega["id_entrega"] = id_entrega

        return new_entrega

    for i in range(200):
        input_pe["entregas"].append(create_huge_entrega(f"unique-key-{i}"))

    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/555",
                          json=input_pe,
                          headers=header_usr_1)

    assert response.status_code == status.HTTP_200_OK

@pytest.mark.parametrize("nome_entrega", 
                         "nome_vinculacao_cadeia_valor",
                         "nome_vinculacao_planejamento", 
                         "nome_demandante", 
                         "nome_destinatario"
                            [
                                ("x" * 299, "x" * 299, "x" * 299, "x" * 299, "x" * 299),
                            ]
                        )
def test_create_pe_longtext(truncate_pe,
                            input_pe: dict,
                            header_usr_1: dict,
                            nome_entrega: str,
                            nome_vinculacao_cadeia_valor: str,
                            nome_vinculacao_planejamento: str,
                            nome_demandante: str,
                            nome_destinatario: str,
                            client: Client):
    """Tenta criar uma entrega com campos de texto preenchidos maiores que o limite (300)"""

    assert 1 == 0 




@pytest.mark.parametrize("missing_fields",
                            fields_plano_entregas["mandatory"])
def test_patch_plano_entrega_inexistente(truncate_pe,
                                            input_pe: dict,
                                            missing_fields: list,
                                            header_usr_1: dict,
                                            client: Client):
    """Tenta atualizar um plano de entrega com PATCH, faltando campos
    obrigatórios.

    Com o verbo PATCH, os campos omitidos são interpretados como sem
    alteração. Por isso, é permitido omitir os campos obrigatórios.

    TODO: Validar necessidade
    """
    for field in missing_fields:
        del input_pe[field]

    input_pe["id_plano_entrega_unidade"] = 999 # precisa ser um plano inexistente
    response = client.patch(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/{input_pe['id_plano_entrega_unidade']}",
                          json=input_pe,
                          headers=header_usr_1)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_create_plano_entrega_same_date_interval(truncate_pe,
                                            input_pe: dict,
                                            header_usr_1: dict,
                                            client: Client):
    """Tenta criar uma plano de entregas no mesmo intervalo de data
    TODO: Validar Regra Negocial - Pode existir mais de um plano por unidade no mesmo período?"""
    assert 1 == 0 


def test_create_pe_cod_plano_inconsistent(input_pe: dict,
                                          header_usr_1: dict,
                                          truncate_pe,
                                          client: Client):
    """Tenta criar um plano de entrega com código de plano divergente"""

    input_pe["id_plano_entrega_unidade"] = 110
    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/111", # diferente de 110
                          json=input_pe,
                          headers=header_usr_1)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro id_plano_entrega_unidade diferente do conteúdo do JSON"
    assert response.json().get("detail", None) == detail_msg

def test_create_pe_cod_unidade_inconsistent(input_pe: dict,
                                          header_usr_1: dict,
                                          truncate_pe,
                                          client: Client):
    """Tenta criar um plano de entrega com código de unidade divergente"""

    input_pe["cod_SIAPE_unidade_plano"] = 999
    response = client.put(f"/plano_entrega/990/1", # diferente de 999
                          json=input_pe,
                          headers=header_usr_1)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro cod_SIAPE_unidade_plano diferente do conteúdo do JSON"
    assert response.json().get("detail", None) == detail_msg

def test_get_plano_entrega(header_usr_1: dict,
                            truncate_pe,
                            example_pe,
                            client: Client):
    """Tenta buscar um plano de entrega existente"""

    response = client.get("/plano_entrega/{input_pe["cod_SIAPE_unidade_plano"]}/555",
                          headers=header_usr_1)
    assert response.status_code == status.HTTP_200_OK

def test_get_pe_inexistente(header_usr_1: dict, client: Client):
    """Tenta buscar um plano de entrega inexistente"""

    response = client.get("/plano_entrega/888888888",
                          headers=header_usr_1)
    assert response.status_code == 404

    assert response.json().get("detail", None) == "Plano de entrega' não encontrado"

@pytest.mark.parametrize("data_inicio_plano_entregas, data_termino_plano_entregas, id_plano_entrega_unidade",
                          [
                            ("2020-06-04", "2020-04-01", "77"),
                            ])
def test_create_pe_mixed_dates(input_pe: dict,
                                 data_inicio: str,
                                 data_fim: str,
                                 cod_plano: str,
                                 header_usr_1: dict,
                                 truncate_pe,
                                 client: Client):
    """Tenta criar um plano de entrega com datas trocadas"""

    input_pe["data_inicio"] = data_inicio
    input_pe["data_fim"] = data_fim
    input_pe["id_plano_entrega_unidade"] = cod_plano

    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/{cod_plano}",
                          json=input_pe,
                          headers=header_usr_1)
    if data_inicio > data_fim:
        assert response.status_code == 422
        detail_msg = "Data fim do Plano de Entregas deve ser maior" \
                     " ou igual que Data de início."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


def test_create_invalid_data_entrega(truncate_pe,
                                            input_pe: dict,
                                            header_usr_1: dict,
                                            client: Client):
    """Tenta criar uma entrega com data de entrega fora do intervalo do plano de entrega
    TODO: Validar Regra Negocial - Pode existir entrega com data fora do intervalo do Plano de Entregas?"""
    assert 1 == 0 



@pytest.mark.parametrize(
        "data_inicio_plano_entregas, data_avaliacao_plano_entregas, id_plano_entrega_unidade",
        [
        ("2020-06-04", "2020-04-01", "77")
        ]  
    )
def test_create_pt_invalid_data_avaliacao(input_pe: dict,
                                          data_inicio_plano_entregas: str,
                                          data_avaliacao_plano_entregas: str,
                                          id_plano_entrega_unidade: int,
                                          header_usr_1: dict,
                                          truncate_pe,
                                          client: Client):
    """Tenta criar um plano de entrega com datas de avaliação inferior a data de inicio do Plano"""
    """TODO: Regra Negocial - A mesma regra deve ser feita com a data de término do Plano?"""

    input_pe["data_inicio_plano_entregas"] = data_inicio_plano_entregas
    input_pe["data_avaliacao_plano_entregas"] = data_avaliacao_plano_entregas
    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade

    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/{id_plano_entrega_unidade}",
                          json=input_pe,
                          headers=header_usr_1)
    if data_inicio_plano_entregas > data_avaliacao_plano_entregas
        assert response.status_code == 422
        detail_msg = "Data de avaliação do Plano de Entrega deve ser maior ou igual" \
                     " que a Data de início do Plano de Entrega."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.parametrize("id_plano_entrega_unidade, id_ent_1, id_ent_2",
                          [
                            ("90", 401, 402),
                            ("91", 403, 403), # <<<< IGUAIS
                            ("92", 404, 404), # <<<< IGUAIS
                            ("93", 405, 406),
                            ])
def test_create_pe_duplicate_entrega(input_pe: dict,
                                       id_plano_entrega_unidade: str,
                                       id_ent_1: str,
                                       id_ent_2: str,
                                       header_usr_1: dict,
                                       truncate_pe,
                                       client: Client):
    """Tenta criar um plano de entrega com entregas com id_entrega duplicados"""

    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    input_pe["entregas"][0]["id_entrega"] = id_ent_1
    input_pe["entregas"][1]["id_entrega"] = id_ent_2

    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/{id_plano_entrega_unidade}",
                          json=input_pe,
                          headers=header_usr_1)
    if id_ent_1 == id_ent_2:
        assert response.status_code == 422
        detail_msg = "Entregas devem possuir id_entrega diferentes."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.parametrize("cod_plano, modalidade_execucao",
                          [
                            ("556", -1),
                            ("81", -2),
                            ("82", -3)
                            ])
def test_create_pt_invalid_modalidade_execucao(input_pt: dict,
                               cod_plano: str,
                               modalidade_execucao: int,
                               header_usr_1: dict,
                               truncate_pt,
                               client: Client):
    input_pt["cod_plano"] = cod_plano
    input_pt["modalidade_execucao"] = modalidade_execucao
    response = client.put(f"/plano_trabalho/{cod_plano}",
                          json=input_pt,
                          headers=header_usr_1)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "value is not a valid enumeration member; permitted: 1, 2, 3"
    assert response.json().get("detail")[0]["msg"] == detail_msg

# @pytest.mark.parametrize(
#     "id_atividade, nome_atividade, faixa_complexidade, "\
#     "tempo_presencial_estimado, tempo_presencial_programado, "\
#     "tempo_teletrabalho_estimado, tempo_teletrabalho_programado",
#                     [
#                         (None, "asd", "asd", 0.0, 0.0, 0.0, 0.0),
#                         ("123123", None, "asd", 0.0, 0.0, 0.0, 0.0),
#                         ("123123", "asd", None, 0.0, 0.0, 0.0, 0.0),
#                         ("123123", "asd", "asd", None, 0.0, 0.0, 0.0),
#                         ("123123", "asd", "asd", 0.0, None, 0.0, 0.0),
#                         ("123123", "asd", "asd", 0.0, 0.0, None, 0.0),
#                         ("123123", "asd", "asd", 0.0, 0.0, 0.0, None),
#                     ])
# def test_create_pt_missing_mandatory_fields_atividade(input_pt: dict,

#                                            id_atividade: str,
#                                            nome_atividade: str,
#                                            faixa_complexidade: str,
#                                            tempo_presencial_estimado: float,
#                                            tempo_presencial_programado: float,
#                                            tempo_teletrabalho_estimado: float,
#                                            tempo_teletrabalho_programado: float,

#                                            header_usr_1: dict,
#                                            truncate_pt,
#                                            client: Client):
#     cod_plano = "111222333"
#     input_pt["cod_plano"] = cod_plano
#     input_pt["atividades"][0]["id_atividade"] = id_atividade
#     input_pt["atividades"][0]["nome_atividade"] = nome_atividade
#     input_pt["atividades"][0]["faixa_complexidade"] = faixa_complexidade
#     input_pt["atividades"][0]["tempo_presencial_estimado"] = tempo_presencial_estimado
#     input_pt["atividades"][0]["tempo_presencial_programado"] = tempo_presencial_programado
#     input_pt["atividades"][0]["tempo_teletrabalho_estimado"] = tempo_teletrabalho_estimado
#     input_pt["atividades"][0]["tempo_teletrabalho_programado"] = tempo_teletrabalho_programado

#     response = client.put(f"/plano_trabalho/{cod_plano}",
#                           json=input_pt,
#                           headers=header_usr_1)
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     detail_msg = "none is not an allowed value"
#     assert response.json().get("detail")[0]["msg"] == detail_msg

def test_create_pe_duplicate_id_plano(input_pe: dict,
                                        header_usr_1: dict,
                                        header_usr_2: dict,
                                        truncate_pe,
                                        client: Client):
    """Tenta criar um plano de entregas duplicados"""

    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/555",
                          json=input_pe,
                          headers=header_usr_1)
    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/555",
                          json=input_pe,
                          headers=header_usr_2)

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_pe

def test_create_invalid_cod_siape_unidade(truncate_pe,
                                            input_pe: dict,
                                            header_usr_1: dict,
                                            client: Client):
    """Tenta criar uma entrega com código SIAPE inválido
    TODO: Validar Regra Negocial - Como será feita a validação com a Integração SIAPE?"""
    assert 1 == 0 

def test_create_entrega_invalid_percent(truncate_pe,
                                            input_pe: dict,
                                            header_usr_1: dict,
                                            client: Client):
    """Tenta criar um Plano de Entrega com entrega com percentuais inválidos"""
    assert 1 == 0 


def test_create_entrega_invalid_tipo_meta(truncate_pe,
                                            input_pe: dict,
                                            header_usr_1: dict,
                                            client: Client):
    """Tenta criar um Plano de Entrega com tipo de meta inválido"""
    assert 1 == 0     


@pytest.mark.parametrize("avaliacao_plano_entregas",
                          [
                            (0),
                            (-1),
                            (6)
                            ])
def test_create_pe_invalid_avaliacao(input_pe: dict,
                               avaliacao_plano_entregas: int,
                               header_usr_1: dict,
                               truncate_pe,
                               client: Client):
    """Tenta criar um Plano de Entrega com nota de avaliação inválida"""

    input_pe["avaliacao_plano_entregas"] = avaliacao_plano_entregas
    response = client.put(f"/plano_entrega/{input_pe['cod_SIAPE_unidade_plano']}/555",
                          json=input_pe,
                          headers=header_usr_1)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Nota de avaliação inválida; permitido: 1, 2, 3, 4, 5"    
    #detail_msg = "value is not a valid enumeration member; permitted: 1, 2, 3, 4, 5"
    assert response.json().get("detail")[0]["msg"] == detail_msg