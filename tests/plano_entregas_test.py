"""
Testes relacionados ao Plano de Entregas da Unidade
"""
from datetime import date, timedelta

from httpx import Client

from fastapi import status

import pytest

# grupos de campos opcionais e obrigatórios a testar

fields_plano_entregas = {
    "optional": (
        ["cancelado", "avaliacao_plano_entregas", "data_avaliacao_plano_entregas"],
    ),
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
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get("detail", None) is None
    assert all(
        response.json()[attribute] == input_pe[attribute]
        for attributes in fields_plano_entregas["mandatory"]
        for attribute in attributes
        if attribute not in ("contribuicoes", "consolidacoes")
    )


def test_create_plano_entregas_unidade_nao_permitida(
    input_pe: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um novo Plano de Entregas em uma organização na qual
    ele não está autorizado.
    """
    response = client.put(
        f"/organizacao/2"  # só está autorizado na organização 1
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        response.json().get("detail", None)
        == "Usuário não tem permissão na cod_SIAPE_instituidora informada"
    )


def test_update_plano_entregas(
    input_pe: dict,
    example_pe,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um novo plano de entregas e atualizar alguns campos.
    A fixture example_pe cria um novo Plano de Entrega na API.
    O teste altera um campo do PE e reenvia pra API (update).
    """

    input_pe["avaliacao_plano_entregas"] = 3
    input_pe["data_avaliacao_plano_entregas"] = "2023-08-15"
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
    assert response.json()["avaliacao_plano_entregas"] == 3
    assert response.json()["data_avaliacao_plano_entregas"] == "2023-08-15"

    # Consulta API para conferir se a alteração foi persistida
    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
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
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert all(
        response.json()[attribute] == input_pe[attribute]
        for attributes in fields_plano_entregas["mandatory"]
        for attribute in attributes
        if attribute not in ("entregas")
    )


@pytest.mark.parametrize(
    "missing_fields", enumerate(fields_plano_entregas["mandatory"])
)
def test_create_plano_entregas_missing_mandatory_fields(
    input_pe: dict,
    missing_fields: list,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entregas, faltando campos obrigatórios.
    Na atualização com PUT, ainda assim é necessário informar todos os
    campos obrigatórios, uma vez que o conteúdo será substituído.
    """
    offset, field_list = missing_fields
    for field in field_list:
        del input_pe[field]

    # para usar na URL, necessário existir caso tenha sido removido
    # como campo obrigatório
    id_plano_entrega_unidade = 1800 + offset
    if input_pe.get("id_plano_entrega_unidade", None):
        # Atualiza o id_plano_entrega_unidade somente se existir.
        # Se não existir, é porque foi removido como campo obrigatório.
        input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_huge_plano_entregas(
    input_pe: dict,
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    client: Client,
):
    """Testa a criação de um plano de entregas com grande volume de dados."""

    def create_huge_entrega(id_entrega: int):
        new_entrega = input_pe["entregas"][0].copy()
        new_entrega["id_entrega"] = 3 + id_entrega
        new_entrega["nome_entrega"] = "x"  * 1000000  # 1mi de caracteres
        new_entrega["nome_demandante"] = "x"  * 1000000  # 1mi de caracteres
        new_entrega["nome_destinatario"] = "x"  * 1000000  # 1mi de caracteres

        return new_entrega

    for id_entrega in range(200):
        input_pe["entregas"].append(create_huge_entrega(id_entrega))

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    # Compara o conteúdo do plano de entregas, somente campos obrigatórios
    assert response.status_code == status.HTTP_201_CREATED
    assert all(
        response.json()[attribute] == input_pe[attribute]
        for attributes in fields_plano_entregas["mandatory"]
        for attribute in attributes
        if attribute not in ("entrega")
    )

    # Compara o conteúdo de cada entrega, somente campos obrigatórios
    response_by_entrega = {
        id_entrega: entrega for entrega in response.json()["entregas"]
    }
    input_by_entrega = {
        id_entrega: entrega for entrega in input_pe["entregas"]
    }
    assert all(
        response_by_entrega[id_entrega][attribute] == entrega[attribute]
        for attributes in fields_entrega["mandatory"]
        for attribute in attributes
        for id_entrega, entrega in input_by_entrega.items()
    )


# TODO: verbo PATCH poderá ser implementado em versão futura.abs
#
# @pytest.mark.parametrize("missing_fields", fields_plano_entregas["mandatory"])
# def test_patch_plano_entregas_inexistente(
#     truncate_pe,
#     input_pe: dict,
#     missing_fields: list,
#     user1_credentials: dict,
#     header_usr_1: dict,
#     client: Client,
# ):
#     """Tenta atualizar um plano de entrega com PATCH, faltando campos
#     obrigatórios.

#     Com o verbo PATCH, os campos omitidos são interpretados como sem
#     alteração. Por isso, é permitido omitir os campos obrigatórios.
#     """
#     example_pe = input_pe.copy()
#     for field in missing_fields:
#         del input_pe[field]

#     input_pe["id_plano_entrega_unidade"] = 999  # precisa ser um plano inexistente
#     response = client.patch(
#         f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
#         f"/plano_entregas/{example_pe['id_plano_entrega_unidade']}",
#         json=input_pe,
#         headers=header_usr_1,
#     )
#     assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, cod_SIAPE_unidade_plano, "
    "data_inicio_plano_entregas, data_termino_plano_entregas",
    [
        (101, 99, "2023-01-01", "2023-06-30"),  # igual ao exemplo
        (102, 99, "2023-07-01", "2023-12-31"),  # sem sobreposição
        (103, 99, "2022-12-01", "2023-01-31"),  # sobreposição no início
        (104, 99, "2023-06-01", "2023-11-30"),  # sobreposição no fim
        (105, 99, "2023-02-01", "2023-05-31"),  # contido no período
        (106, 99, "2022-12-01", "2023-07-31"),  # contém o período
        (105, 100, "2023-02-01", "2023-05-31"),  # outra unidade
    ],
)
def test_create_plano_entregas_overlapping_date_interval(
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
    """Tenta criar um plano de entregas com sobreposição de intervalo de
    data na mesma unidade.

    O Plano de Entregas original é criado e então é testada a criação de
    cada novo Plano de Entregas, com sobreposição ou não das datas,
    conforme especificado nos parâmetros de teste.
    """
    original_pe = input_pe.copy()

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=original_pe,
        headers=header_usr_1,
    )

    assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)

    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    input_pe["cod_SIAPE_unidade_plano"] = cod_SIAPE_unidade_plano
    input_pe["data_inicio_plano_entregas"] = data_inicio_plano_entregas
    input_pe["data_termino_plano_entregas"] = data_termino_plano_entregas

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if (
        # se algum dos planos estiver cancelado, não há problema em haver
        # sobreposição
        not any((plano.get("cancelado", False) for plano in (input_pe, original_pe)))
        and input_pe["cod_SIAPE_unidade_plano"]
        == original_pe["cod_SIAPE_unidade_plano"]
    ):
        if (
            date.fromisoformat(input_pe["data_inicio_plano_entregas"])
            < date.fromisoformat(original_pe["data_termino_plano_entregas"])
        ) and (
            date.fromisoformat(input_pe["data_termino_plano_entregas"])
            > date.fromisoformat(original_pe["data_inicio_plano_entregas"])
        ):
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_msg = (
                "Já existe um plano de entregas para este "
                "cod_SIAPE_unidade_plano no período informado."
            )
            assert response.json().get("detail", None) == detail_msg

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == input_pe


@pytest.mark.parametrize(
    "data_inicio_plano_entregas, data_termino_plano_entregas",
    [
        ("2023-01-01", "2023-06-30"),  # igual ao exemplo
        ("2023-01-01", "2024-01-01"),  # um ano
        ("2023-01-01", "2024-01-02"),  # mais que um ano
    ],
)
def test_create_plano_entregas_date_interval_over_a_year(
    truncate_pe,
    input_pe: dict,
    data_inicio_plano_entregas: str,
    data_termino_plano_entregas: str,
    user1_credentials: dict,
    header_usr_1: dict,
    client: Client,
):
    """Plano de Entregas não pode ter vigência superior a um ano."""
    input_pe["data_inicio_plano_entregas"] = data_inicio_plano_entregas
    input_pe["data_termino_plano_entregas"] = data_termino_plano_entregas

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if date.fromisoformat(data_termino_plano_entregas) - date.fromisoformat(
        data_inicio_plano_entregas
    ) > timedelta(days=366):
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_msg = "Plano de entregas não pode abranger período maior que " "1 ano."
        assert response.json().get("detail", None) == detail_msg
    else:
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == input_pe


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
        f"/plano_entregas/111",  # diferente de 110
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

    input_pe["cod_SIAPE_instituidora"] = 999
    response = client.put(
        f"/organizacao/1000"  # diferente de 999
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    detail_msg = "Parâmetro cod_SIAPE_instituidora na URL e no JSON devem ser iguais"
    assert response.json().get("detail", None) == detail_msg


def test_get_plano_entrega(
    user1_credentials: dict,
    header_usr_1: dict,
    truncate_pe,
    input_pe,
    example_pe,
    client: Client
):
    """Tenta buscar um plano de entrega existente"""

    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_pe_inexistente(
    user1_credentials: dict, header_usr_1: dict, client: Client
):
    """Tenta buscar um plano de entrega inexistente"""

    response = client.get(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        "/plano_entregas/888888888",
        headers=header_usr_1,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert response.json().get("detail", None) == "Plano de entregas não encontrado"


@pytest.mark.parametrize(
    "data_inicio, data_fim",
    [
        ("2020-06-04", "2020-04-01"),
    ],
)
def test_create_pe_invalid_period(
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
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )
    if data_inicio > data_fim:
        assert response.status_code == 422
        detail_message = (
            "Data fim do Plano de Entregas deve ser maior"
            " ou igual que Data de início."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, data_inicio_plano_entregas, "
    "data_termino_plano_entregas, data_entrega",
    [
        (91, "2023-08-01", "2023-09-01", "2023-08-08"),
        (92, "2023-08-01", "2023-09-01", "2023-07-01"),
        (93, "2023-08-01", "2023-09-01", "2023-10-01"),
    ],
)
def test_create_data_entrega_out_of_bounds(
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
    """Tenta criar uma entrega com data de entrega fora do intervalo do plano de entrega"""
    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade
    input_pe["data_inicio_plano_entregas"] = data_inicio_plano_entregas
    input_pe["data_termino_plano_entregas"] = data_termino_plano_entregas
    input_pe["entregas"][0]["data_entrega"] = data_entrega

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )
    if (
        data_entrega < data_inicio_plano_entregas
        or data_entrega > data_termino_plano_entregas
    ):
        assert response.status_code == 422
        detail_message = (
            "Data de entrega precisa estar dentro do intervalo entre início "
            "e término do Plano de Entregas."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, data_inicio_plano_entregas, data_avaliacao_plano_entregas",
    [
        (77, "2020-06-04", "2020-04-01"),
        (78, "2020-06-04", "2020-06-11"),
    ],
)
def test_create_pe_invalid_data_avaliacao(
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

    input_pe["data_inicio_plano_entregas"] = data_inicio_plano_entregas
    input_pe["data_avaliacao_plano_entregas"] = data_avaliacao_plano_entregas
    input_pe["id_plano_entrega_unidade"] = id_plano_entrega_unidade

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )
    if data_avaliacao_plano_entregas < data_inicio_plano_entregas:
        assert response.status_code == 422
        detail_message = (
            "Data de avaliação do Plano de Entrega deve ser maior ou igual"
            " que a Data de início do Plano de Entrega."
        )
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


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
        f"/plano_entregas/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )
    if id_ent_1 == id_ent_2:
        assert response.status_code == 422
        detail_message = "Entregas devem possuir id_entrega diferentes."
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
    else:
        assert response.status_code == status.HTTP_201_CREATED


def test_create_pe_duplicate_id_plano(
    input_pe: dict,
    user1_credentials: dict,
    user2_credentials: dict,
    header_usr_1: dict,
    header_usr_2: dict,
    truncate_pe,
    client: Client,
):
    """Tenta criar um plano de entregas duplicado. O envio do mesmo
    plano de entregas pela segunda vez deve substituir o primeiro.
    """

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    assert response.status_code == status.HTTP_201_CREATED

    response = client.put(
        f"/organizacao/{user2_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_2,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("detail", None) is None
    assert response.json() == input_pe


@pytest.mark.parametrize("cod_SIAPE_unidade_plano", [99, 0, -1])
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
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if cod_SIAPE_unidade_plano > 0:
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "cod_SIAPE_unidade_plano inválido"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


@pytest.mark.parametrize(
    "id_plano_entrega_unidade, meta_entrega, percentual_progresso_esperado, percentual_progresso_realizado",
    [
        (555, 101, 99, 100),
        (556, 100, 101, 0),
        (557, 1, 100, 101),
        (558, 100, 100, 100),
        (559, 100, -1, 0),
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

    input_pe["entregas"][1]["meta_entrega"] = meta_entrega
    input_pe["entregas"][1][
        "percentual_progresso_esperado"
    ] = percentual_progresso_esperado
    input_pe["entregas"][1][
        "percentual_progresso_realizado"
    ] = percentual_progresso_realizado

    response = client.put(
        f"/organizacao/{user1_credentials['cod_SIAPE_instituidora']}"
        f"/plano_entregas/{id_plano_entrega_unidade}",
        json=input_pe,
        headers=header_usr_1,
    )

    if all(
        (0 <= percent <= 100)
        for percent in (
            meta_entrega,
            percentual_progresso_esperado,
            percentual_progresso_realizado,
        )
    ):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Valor percentual inválido."
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


@pytest.mark.parametrize("tipo_meta", [0, 1, 2, 3, 10])
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
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if tipo_meta in (1, 2):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Tipo de meta inválido; permitido: 1, 2"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )


@pytest.mark.parametrize("avaliacao_plano_entregas", [-1, 0, 1, 6])
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
        f"/plano_entregas/{input_pe['id_plano_entrega_unidade']}",
        json=input_pe,
        headers=header_usr_1,
    )

    if avaliacao_plano_entregas in range(1, 6):
        assert response.status_code == status.HTTP_201_CREATED
    else:
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        detail_message = "Nota de avaliação inválida; permitido: 1, 2, 3, 4, 5"
        assert any(
            f"Value error, {detail_message}" in error["msg"]
            for error in response.json().get("detail")
        )
