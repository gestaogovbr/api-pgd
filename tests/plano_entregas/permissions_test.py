"""Testes relacionados às permissões de uso dos endpoints do Plano de
Entregas.
"""

from fastapi import status as http_status

from .core_test import BasePETest


class TestPermissionsPE(BasePETest):
    """Testes relacionados a permissões e acesso ao Plano de Entregas de diferentes unidades."""

    def test_get_plano_entregas_different_unit(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        example_pe_unidade_3,  # pylint: disable=unused-argument
        header_usr_2: dict,
    ):
        """Tenta buscar um plano de entregas existente em uma unidade diferente,
        à qual o usuário não tem acesso.
        """
        input_pe = self.input_pe.copy()
        response = self.get_plano_entregas(
            input_pe["id_plano_entregas"],
            3,  # Sem autorização nesta unidade
            header_usr=header_usr_2,
        )
        assert response.status_code == http_status.HTTP_403_FORBIDDEN

    def test_get_plano_entregas_different_unit_admin(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        example_pe_unidade_3,  # pylint: disable=unused-argument
        header_admin: dict,
        admin_credentials: dict,
    ):
        """Tenta, como administrador, buscar um Plano de Entregas
        em uma organização diferente da sua própria organização.
        """
        input_pe = self.input_pe.copy()
        input_pe["cod_unidade_autorizadora"] = 3

        response = self.client.get(
            f"/user/{admin_credentials['username']}",
            headers=header_admin,
        )

        # Verifica se o usuário é admin e se está em outra unidade
        assert response.status_code == http_status.HTTP_200_OK
        admin_data = response.json()
        assert (
            admin_data.get("cod_unidade_autorizadora", None)
            != input_pe["cod_unidade_autorizadora"]
        )
        assert admin_data.get("is_admin", None) is True

        response = self.get_plano_entregas(
            input_pe["id_plano_entregas"],
            input_pe["cod_unidade_autorizadora"],
            header_usr=header_admin,
        )

        assert response.status_code == http_status.HTTP_200_OK

    def test_put_plano_entregas_different_unit_admin(
        self,
        truncate_pe,  # pylint: disable=unused-argument
        header_admin: dict,
        admin_credentials: dict,
    ):
        """Tenta, como administrador, criar um novo Plano de Entregas
        em uma organização diferente da sua própria organização.
        """
        input_pe = self.input_pe.copy()
        input_pe["cod_unidade_autorizadora"] = 3  # Unidade diferente

        response = self.client.get(
            f"/user/{admin_credentials['username']}",
            headers=header_admin,
        )

        # Verifica se o usuário é admin e se está em outra unidade
        assert response.status_code == http_status.HTTP_200_OK
        admin_data = response.json()
        assert (
            admin_data.get("cod_unidade_autorizadora", None)
            != input_pe["cod_unidade_autorizadora"]
        )
        assert admin_data.get("is_admin", None) is True

        response = self.put_plano_entregas(
            input_pe,
            cod_unidade_autorizadora=input_pe["cod_unidade_autorizadora"],
            id_plano_entregas=input_pe["id_plano_entregas"],
            header_usr=header_admin,
        )

        assert response.status_code == http_status.HTTP_201_CREATED
        assert response.json().get("detail", None) is None
        self.assert_equal_plano_entregas(response.json(), input_pe)
