"""Testes relacionados a verificações de datas associadas ao Plano de
Entregas.
"""

from copy import deepcopy
from datetime import date

from fastapi import status as http_status

import pytest

from util import over_a_year
from .core_test import BasePETest
from tests.conftest import PT_PE_UPDATE_YEAR_VALIDATION_CUTOFF_DATE

# Datas básicas


class TestPlanoDeDatasBasicas(BasePETest):
    """Testes de Plano de Entregas com datas básicas."""

    @pytest.mark.parametrize(
        "data_inicio, data_termino",
        [
            ("2024-01-01", "2024-06-30"),  # igual ao exemplo
            ("2024-01-01", "2025-01-01"),  # um ano
            ("2024-01-01", "2025-01-02"),  # mais que um ano
        ],
    )
    def test_create_plano_entregas_date_interval_over_a_year(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        data_inicio: str,
        data_termino: str,
    ):
        """Plano de Entregas não pode ter vigência superior a um ano."""

        input_pe = deepcopy(self.input_pe)
        input_pe["data_inicio"] = data_inicio
        input_pe["data_termino"] = data_termino

        response = self.put_plano_entregas(input_pe)

        if (
            over_a_year(
                date.fromisoformat(data_inicio), date.fromisoformat(data_termino)
            )
            == 1
        ):
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "Plano de entregas não pode abranger período maior que 1 ano"
            )
            assert response.json().get("detail") == detail_message
        else:
            assert response.status_code == http_status.HTTP_201_CREATED
            self.assert_equal_plano_entregas(response.json(), input_pe)

    @pytest.mark.parametrize(
        "data_inicio, data_termino",
        [
            ("2024-01-01", "2025-01-02", ),  # antes da data de corte (permitido)
            ("2025-06-01", "2026-06-02"),  # após da data de corte (proibido)
        ],
    )
    def test_update_plano_entregas_date_interval_over_a_year(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        data_inicio: str,
        data_termino: str,
    ):
        """Plano de Entregas não pode ter vigência superior a um ano."""
        self.put_plano_entregas(self.input_pe)
        input_pe2 = deepcopy(self.input_pe)
        input_pe2["data_inicio"] = data_inicio
        input_pe2["data_termino"] = data_termino
        # para evitar erro de data_avaliacao < data_inicio
        input_pe2["data_avaliacao"] = data_inicio

        response = self.put_plano_entregas(input_pe2)

        if (
            over_a_year(
                date.fromisoformat(data_inicio), date.fromisoformat(data_termino)
            )
            == 1 and date.fromisoformat(data_inicio) > PT_PE_UPDATE_YEAR_VALIDATION_CUTOFF_DATE
        ):
            assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
            detail_message = (
                "Plano de entregas não pode abranger período maior que 1 ano"
            )
            assert response.json().get("detail") == detail_message
        else:
            assert response.status_code == http_status.HTTP_200_OK
            self.assert_equal_plano_entregas(response.json(), input_pe2)



    @pytest.mark.parametrize(
        "data_inicio, data_termino",
        [
            ("2020-06-04", "2020-04-01"),
        ],
    )
    def test_create_pe_invalid_period(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        data_inicio: str,
        data_termino: str,
    ):
        """Tenta criar um plano de entregas com datas trocadas"""

        input_pe = deepcopy(self.input_pe)
        input_pe["data_inicio"] = data_inicio
        input_pe["data_termino"] = data_termino

        response = self.put_plano_entregas(input_pe)
        if data_inicio > data_termino:
            assert response.status_code == 422
            detail_message = "data_termino deve ser maior ou igual que data_inicio."
            assert any(
                f"Value error, {detail_message}" in error["msg"]
                for error in response.json().get("detail")
            )
        else:
            assert response.status_code == http_status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        "id_plano_entregas, data_inicio, data_avaliacao",
        [
            ("77", "2024-06-04", "2024-04-01"),
            ("78", "2024-06-04", "2024-06-11"),
        ],
    )
    def test_create_pe_invalid_data_avaliacao(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        data_inicio: str,
        data_avaliacao: str,
        id_plano_entregas: str,
    ):
        """Tenta criar um Plano de Entregas com datas de avaliação inferior a
        data de inicio do plano."""

        input_pe = deepcopy(self.input_pe)
        input_pe["data_inicio"] = data_inicio
        input_pe["data_avaliacao"] = data_avaliacao
        input_pe["id_plano_entregas"] = id_plano_entregas

        response = self.put_plano_entregas(input_pe)

        if data_avaliacao < data_inicio:
            assert response.status_code == 422
            detail_message = "data_avaliacao deve ser maior ou igual à data_inicio."
            assert any(
                f"Value error, {detail_message}" in error["msg"]
                for error in response.json().get("detail")
            )
        else:
            assert response.status_code == http_status.HTTP_201_CREATED


# Entregas


class TestPlanoDeDatasEntregas(BasePETest):
    """Testes de Plano de Entregas com datas de entregas."""

    @pytest.mark.parametrize(
        "id_plano_entregas, data_inicio, data_termino, data_entrega",
        [
            ("91", "2024-08-01", "2024-09-01", "2024-08-08"),  # dentro
            ("92", "2024-08-01", "2024-09-01", "2024-07-01"),  # antes do início
            ("93", "2024-08-01", "2024-09-01", "2024-10-01"),  # depois do fim
        ],
    )
    def test_create_data_entrega_out_of_bounds(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        id_plano_entregas: str,
        data_inicio: str,
        data_termino: str,
        data_entrega: str,
    ):
        """Tenta criar uma entrega com data de entrega dentro e fora do
        intervalo do plano de entregas. Segundo as regras de negócio, essa
        data pode ser qualquer data e não precisa estar dentro do período
        entre o início e o fim do plano_entregas.
        """
        input_pe = deepcopy(self.input_pe)
        input_pe["id_plano_entregas"] = id_plano_entregas
        input_pe["data_inicio"] = data_inicio
        input_pe["data_termino"] = data_termino
        for entrega in input_pe["entregas"]:
            entrega["data_entrega"] = data_entrega

        response = self.put_plano_entregas(input_pe)
        # Aceitar em todos os casos
        assert response.status_code == http_status.HTTP_201_CREATED

    @pytest.mark.parametrize(
        "id_plano_entregas, cod_unidade_executora, data_inicio, data_termino, status",
        [
            ("11", 99, "2024-01-01", "2024-06-30", 4),  # igual ao exemplo
            ("12", 99, "2025-01-01", "2025-06-30", 4),  # sem sobreposição
            ("13", 99, "2023-12-01", "2024-01-31", 4),  # sobreposição no início
            ("14", 99, "2024-12-01", "2025-01-31", 4),  # sobreposição no fim
            ("15", 99, "2024-02-01", "2024-05-31", 4),  # contido no período
            ("16", 99, "2023-12-01", "2024-07-31", 4),  # contém o período
            ("17", 100, "2024-02-01", "2024-05-31", 4),  # outra unidade
            # sobreposição porém um é cancelado
            ("18", 99, "2023-12-01", "2024-01-31", 1),
        ],
    )
    def test_create_plano_entregas_overlapping_date_interval(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        example_pe,  # pylint: disable=unused-argument
        id_plano_entregas: str,
        cod_unidade_executora: int,
        data_inicio: str,
        data_termino: str,
        status: int,
    ):
        """Tenta criar um plano de entregas cujas entregas têm sobreposição
        de intervalo de data na mesma unidade.

        O Plano de Entregas original é criado e então é testada a criação de
        cada novo Plano de Entregas, com sobreposição ou não das datas,
        conforme especificado nos parâmetros de teste.
        """
        original_pe = self.input_pe.copy()
        input_pe2 = original_pe.copy()
        input_pe2["id_plano_entregas"] = "2"
        input_pe2["data_inicio"] = "2024-07-01"
        input_pe2["data_termino"] = "2024-12-31"
        for entrega in input_pe2["entregas"]:
            entrega["data_entrega"] = "2024-12-31"
        response = self.put_plano_entregas(
            input_pe2,
            cod_unidade_autorizadora=self.user1_credentials["cod_unidade_autorizadora"],
            id_plano_entregas=input_pe2["id_plano_entregas"],
        )
        assert response.status_code == http_status.HTTP_201_CREATED

        input_pe = original_pe.copy()
        input_pe["id_plano_entregas"] = id_plano_entregas
        input_pe["cod_unidade_executora"] = cod_unidade_executora
        input_pe["data_inicio"] = data_inicio
        input_pe["data_termino"] = data_termino
        input_pe["status"] = status
        for entrega in input_pe["entregas"]:
            entrega["data_entrega"] = data_termino
        input_pe["avaliacao"] = None
        input_pe["data_avaliacao"] = None
        response = self.put_plano_entregas(input_pe)
        if (
            # se algum dos planos estiver cancelado, não há problema em haver
            # sobreposição
            input_pe["status"] == 1
            # se são unidades diferentes, não há problema em haver sobreposição
            or input_pe["cod_unidade_executora"] != original_pe["cod_unidade_executora"]
        ):
            # um dos planos está cancelado, pode ser criado
            assert response.status_code == http_status.HTTP_201_CREATED
            self.assert_equal_plano_entregas(response.json(), input_pe)
        else:
            if any(
                (
                    date.fromisoformat(input_pe["data_inicio"])
                    < date.fromisoformat(existing_pe["data_termino"])
                )
                and (
                    date.fromisoformat(input_pe["data_termino"])
                    > date.fromisoformat(existing_pe["data_inicio"])
                )
                for existing_pe in (original_pe, input_pe2)
            ):
                assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
                detail_msg = (
                    "Já existe um plano de entregas para este "
                    "cod_unidade_executora no período informado."
                )
                assert response.json().get("detail", None) == detail_msg
            else:
                # não há sobreposição de datas
                assert response.status_code == http_status.HTTP_201_CREATED
                self.assert_equal_plano_entregas(response.json(), input_pe)
