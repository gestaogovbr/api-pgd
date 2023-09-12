"""
Testes relacionados ao Plano de Entregas da Unidade
"""
import itertools
from datetime import date

from httpx import Client

from fastapi import status

import pytest

# grupos de campos opcionais e obrigatórios a testar

fields_plano_entregas = {
    "optional": (["avaliacao_plano_entregas", "data_avaliacao_plano_entregas"],),
    "mandatory": (
        ["id_plano_entrega_unidade"],
        ["data_inicio_plano_entregas"],
        ["data_termino_plano_entregas"],
        ["cod_SIAPE_unidade_plano"],
        ["entregas"],
    ),
}

fields_entrega = {
    "optional": (
        ["nome_vinculacao_cadeia_valor"],
        ["nome_vinculacao_planejamento"],
        ["percentual_progresso_esperado"],
        ["percentual_progresso_realizado"],
    ),
    "mandatory": (
        ["id_entrega"],
        ["nome_entrega"],
        ["meta_entrega"],
        ["tipo_meta"],
        ["data_entrega"],
        ["nome_demandante"],
        ["nome_destinatario"],
    ),
}


def test_create_plano_entregas_completo(
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um novo plano de entregas"""
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_pe


def test_update_plano_trabalho(
    input_pe: dict,
    example_pe,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um novo plano de entregas e atualizar alguns campos
    A fixture example_pe cria um novo Plano de Entrega na API
    Altera um campo do PE e reenvia pra API (update)
    TODO: Validar regra negocial - No update devem ser enviados as entregas novamente?
    """

    input_pe["avaliacao_plano_entregas"] = 3
    input_pe["data_avaliacao_plano_entregas"] = "2023-08-15"
    client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/555",
        json=input_pe,
        headers=header_usr_1,
    )
    # Consulta API para conferir se a alteração foi persistida
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/555",
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["avaliacao_plano_entregas"] == 3
    assert response.json()["data_avaliacao_plano_entregas"] == "2023-08-15"


@pytest.mark.parametrize("omitted_fields", enumerate(fields_entrega["optional"]))
def test_create_plano_entregas_entrega_omit_optional_fields(
    input_pe: dict,
    omitted_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um novo plano de entregas omitindo campos opcionais"""

    offset, field_list = omitted_fields
    for field in field_list:
        for entrega in input_pe["entregas"]:
            if field in entrega:
                del entrega[field]

    input_pe["id_plano_entrega_unidade"] = 557 + offset
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "missing_fields", enumerate(fields_plano_entregas["mandatory"])
)
def test_create_plano_entrega_missing_mandatory_fields(
    input_pe: dict,
    missing_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entregas, faltando campos obrigatórios.
    Tem que ser um plano de entregas novo, pois na atualização de um
    plano de trabalho existente, o campo que ficar faltando será
    interpretado como um campo que não será atualizado, ainda que seja
    obrigatório para a criação.
    """
    offset, field_list = missing_fields
    example_pe = input_pe.copy()
    for field in field_list:
        del input_pe[field]

    input_pe["id_plano_entrega_unidade"] = 1800 + offset  # precisa ser um novo plano
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{example_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_huge_plano_entrega(
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    def create_huge_entrega(id_entrega: str):
        new_entrega = input_pe["entregas"][0].copy()
        new_entrega["id_entrega"] = id_entrega

        return new_entrega

    for i in range(200):
        input_pe["entregas"].append(create_huge_entrega(f"unique-key-{i}"))

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/555",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("missing_fields", fields_plano_entregas["mandatory"])
def test_patch_plano_entrega_inexistente(
    truncate_pe,
    input_pe: dict,
    missing_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta atualizar um plano de entrega com PATCH, faltando campos
    obrigatórios.

    Com o verbo PATCH, os campos omitidos são interpretados como sem
    alteração. Por isso, é permitido omitir os campos obrigatórios.

    TODO: Validar necessidade
    """
    example_pe = input_pe.copy()
    for field in missing_fields:
        del input_pe[field]

    input_pe["id_plano_entrega_unidade"] = 999  # precisa ser um plano inexistente
    response = client.patch(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{example_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, cod_SIAPE_unidade_plano, "
    "data_inicio_plano_entregas, data_termino_plano_entregas",
    [
        (101, 99, "2023-01-01", "2023-06-30"), # igual
        (102, 99, "2023-07-01", "2023-12-31"), # sem sobreposição
        (103, 99, "2022-12-01", "2023-01-31"), # sobreposição no início
        (104, 99, "2023-06-01", "2023-11-30"), # sobreposição no fim
        (105, 99, "2023-02-01", "2023-05-31"), # contido no período
        (106, 99, "2022-12-01", "2023-07-31"), # contém o período
        (105, 100, "2023-02-01", "2023-05-31"), # outra unidade
    ],
)
def test_create_plano_entrega_overlapping_date_interval(
    truncate_pe,
    input_pe: dict,
    id_plano_entrega_unidade: int,
    cod_SIAPE_unidade_plano: int,
    data_inicio_plano_entregas: str,
    data_termino_plano_entregas: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar uma plano de entregas com sobreposição de intervalo de
    data na mesma unidade.
    TODO: Validar Regra Negocial - Pode existir mais de um plano por unidade no mesmo período?
    """
    original_pe = input_pe.copy()

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_200_OK

    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    input_pe["cod_SIAPE_unidade_plano"] = cod_SIAPE_unidade_plano
    input_pe["data_inicio_plano_entregas"] = data_inicio_plano_entregas
    input_pe["data_termino_plano_entregas"] = data_termino_plano_entregas

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if input_pe["cod_SIAPE_unidade_plano"] == original_pe["cod_SIAPE_unidade_plano"]:
        if (
            input_pe["data_inicio_plano_entregas"]
            < original_pe["data_termino_plano_entregas"]
        ) and (
            input_pe["data_termino_plano_entregas"]
            > original_pe["data_inicio_plano_entregas"]
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "Já existe um plano de entregas para este "
                "cod_SIAPE_unidade_plano no período informado."
            )
            assert response.json().get("detail", None) == detail_msg


def test_create_pe_cod_plano_inconsistent(
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entrega com código de plano divergente"""

    input_pe["id_plano_entrega_unidade"] = 110
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/111",  # diferente de 110
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro id_plano_entrega_unidade diferente do conteúdo do JSON"
    assert response.json().get("detail", None) == detail_msg


def test_create_pe_cod_unidade_inconsistent(
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entrega com código de unidade divergente"""

    input_pe["cod_SIAPE_unidade_plano"] = 999
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/1",
        json=input_pe,
        headers=header_usr_1,  # diferente de 999
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro cod_SIAPE_instituidora na URL diferente do conteúdo do JSON"
    assert response.json().get("detail", None) == detail_msg


def test_get_plano_entrega(
    user1_credentials: dict, header_usr_1: dict, truncate_pe, input_pe, client: Client
):
    """Tenta buscar um plano de entrega existente"""

    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/555",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_pe_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    """Tenta buscar um plano de entrega inexistente"""

    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/plano_entrega/888888888",
        headers=header_usr_1,
    )
    assert response.status_code == 404

    assert response.json().get("detail", None) == "Plano de entrega não encontrado"


@pytest.mark.parametrize(
    "data_inicio, data_fim",
    [
        ("2020-06-04", "2020-04-01"),
    ],
)
def test_create_pe_mixed_dates(
    input_pe: dict,
    data_inicio: str,
    data_fim: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entrega com datas trocadas"""

    input_pe["data_inicio_plano_entregas"] = data_inicio
    input_pe["data_termino_plano_entregas"] = data_fim

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )
    if data_inicio > data_fim:
        assert response.status_code == 422
        detail_msg = (
            "Data fim do Plano de Entregas deve ser maior"
            " ou igual que Data de início."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, data_inicio_plano_entregas, "
    "data_termino_plano_entregas, data_entrega",
    [
        (91, "2023-08-01", "2023-09-01", "2023-08-08"),
        (92, "2023-08-01", "2023-09-01", "2023-07-01"),
        (93, "2023-08-01", "2023-09-01", "2023-10-01"),
    ],
)
def test_create_invalid_data_entrega(
    input_pe: dict,
    id_plano_entrega_unidade: int,
    data_inicio_plano_entregas: str,
    data_termino_plano_entregas: str,
    data_entrega: str,
    truncate_pe,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar uma entrega com data de entrega fora do intervalo do plano de entrega
    TODO: Validar Regra Negocial - Pode existir entrega com data fora do intervalo do Plano de Entregas?
    """
    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    input_pe["data_inicio_plano_entregas"] = data_inicio_plano_entregas
    input_pe["data_termino_plano_entregas"] = data_termino_plano_entregas
    input_pe["entregas"][0]["data_entrega"] = data_entrega

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )
    if (
        data_entrega < data_inicio_plano_entregas
        or data_entrega > data_termino_plano_entregas
    ):
        assert response.status_code == 422
        detail_msg = (
            "Data de entrega precisa estar dentro do intervalo entre início "
            "e término do Plano de Entrega."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, data_inicio_plano_entregas, data_avaliacao_plano_entregas",
    [
        (77, "2020-06-04", "2020-04-01"),
        (78, "2020-06-04", "2020-06-11"),
    ],
)
def test_create_pt_invalid_data_avaliacao(
    input_pe: dict,
    data_inicio_plano_entregas: str,
    data_avaliacao_plano_entregas: str,
    id_plano_entrega_unidade: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entrega com datas de avaliação inferior a data de inicio do Plano"""
    """TODO: Regra Negocial - A mesma regra deve ser feita com a data de término do Plano?"""

    input_pe["data_inicio_plano_entregas"] = data_inicio_plano_entregas
    input_pe["data_avaliacao_plano_entregas"] = data_avaliacao_plano_entregas
    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )
    if data_inicio_plano_entregas > data_avaliacao_plano_entregas:
        assert response.status_code == 422
        detail_msg = (
            "Data de avaliação do Plano de Entrega deve ser maior ou igual"
            " que a Data de início do Plano de Entrega."
        )
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, id_ent_1, id_ent_2",
    [
        (90, 401, 402),
        (91, 403, 403),  # <<<< IGUAIS
        (92, 404, 404),  # <<<< IGUAIS
        (93, 405, 406),
    ],
)
def test_create_pe_duplicate_entrega(
    input_pe: dict,
    id_plano_entrega_unidade: int,
    id_ent_1: str,
    id_ent_2: str,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entrega com entregas com id_entrega duplicados"""

    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    input_pe["entregas"][0]["id_entrega"] = id_ent_1
    input_pe["entregas"][1]["id_entrega"] = id_ent_2

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )
    if id_ent_1 == id_ent_2:
        assert response.status_code == 422
        detail_msg = "Entregas devem possuir id_entrega diferentes."
        assert response.json().get("detail")[0]["msg"] == detail_msg
    else:
        assert response.status_code == status.HTTP_200_OK


def test_create_pe_duplicate_id_plano(
    input_pe: dict,
    user1_credentials: dict,
    user2_credentials: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entregas duplicados"""

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/555",
        json=input_pe,
        headers=header_usr_1,
    )
    response = client.put(
        f"/organizacao/{user2_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/555",
        json=input_pe,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) == None
    assert response.json() == input_pe


@pytest.mark.parametrize(
    "cod_SIAPE_unidade_plano",
    [ (99,), (0,), (-1,) ]
)
def test_create_invalid_cod_siape_unidade(
    truncate_pe,
    input_pe: dict,
    cod_SIAPE_unidade_plano: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar uma entrega com código SIAPE inválido.
    Por ora não será feita validação no sistema, e sim apenas uma
    verificação de sanidade.
    """
    input_pe["cod_SIAPE_unidade_plano"] = cod_SIAPE_unidade_plano

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if cod_SIAPE_unidade_plano > 0:
        assert response.status_code == status.HTTP_200_OK
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, meta_entrega, percentual_progresso_esperado, percentual_progresso_realizado",
    [
        (555, 101, 99, 100),
        (556, 100, 101, 0),
        (557, 1, 100, 101),
        (558, 100, 100, 100),
    ],
)
def test_create_entrega_invalid_percent(
    truncate_pe,
    input_pe: dict,
    id_plano_entrega_unidade: int,
    meta_entrega: int,
    percentual_progresso_esperado: int,
    percentual_progresso_realizado: int,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Tenta criar um Plano de Entrega com entrega com percentuais inválidos"""
    """TODO: Se for tipo_meta absoluta, pode ser superior a 100?"""

    input_pe["entregas"][1]["meta_entrega"] = meta_entrega
    input_pe["entregas"][1]["percentual_progresso_esperado"] = percentual_progresso_esperado
    input_pe["entregas"][1]["percentual_progresso_esperado"] = percentual_progresso_realizado  

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )

    if all((percent >= 0 and percent <= 100)
        for percent in (meta_entrega, percentual_progresso_esperado, percentual_progresso_realizado)):
        assert response.status_code == 200
    else:
        assert response.status_code == 422
        detail_msg = "Valor percentual inválido."
        assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize(
    "tipo_meta",
    [ (0), (3), (10) ]
)
def test_create_entrega_invalid_tipo_meta(
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    tipo_meta: int,
    client: Client,
):
    """Tenta criar um Plano de Entrega com tipo de meta inválido"""
    input_pe["entregas"][0]["tipo_meta"] = tipo_meta

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/555",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == 422
    detail_msg = "Tipo de meta inválido."
    assert response.json().get("detail")[0]["msg"] == detail_msg


@pytest.mark.parametrize("avaliacao_plano_entregas", [(0), (-1), (6)])
def test_create_pe_invalid_avaliacao(
    input_pe: dict,
    avaliacao_plano_entregas: int,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um Plano de Entrega com nota de avaliação inválida"""

    input_pe["avaliacao_plano_entregas"] = avaliacao_plano_entregas
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entrega/555",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Nota de avaliação inválida; permitido: 1, 2, 3, 4, 5"
    # detail_msg = "value is not a valid enumeration member; permitted: 1, 2, 3, 4, 5"
    assert response.json().get("detail")[0]["msg"] == detail_msg
