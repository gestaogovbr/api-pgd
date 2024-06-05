import pytest
from httpx import Client
from fastapi import status

from .core_test import assert_equal_plano_trabalho

class TestGetPlanoDeTrabalhoDiferenteUnidade:
    """
    Testes para verificar o acesso a um plano de trabalho de uma unidade diferente.

    Esses testes verificam o comportamento do sistema quando um usuário tenta acessar
    um plano de trabalho de uma unidade diferente, tanto com um usuário sem permissão
    quanto com um usuário com permissão de administrador.
    """

    @pytest.fixture
    def setup(
        self,
        input_pt: dict,
        header_usr_2: dict,
        header_admin: dict,
        truncate_pt,  # pylint: disable=unused-argument
        truncate_pe, # pylint: disable=unused-argument
        example_pe_unidade_3,  # pylint: disable=unused-argument
        example_pt_unidade_3,  # pylint: disable=unused-argument
        client: Client,
    ):
        """
        Fixture de configuração para os testes da classe
        TestGetPlanoDeTrabalhoDiferenteUnidade.

        Esta fixture inicializa os atributos da classe com os valores
        fornecidos pelos parâmetros.
        """
        # pylint: disable=attribute-defined-outside-init
        self.input_pt = input_pt
        self.header_usr_2 = header_usr_2
        self.header_admin = header_admin
        self.client = client

    def test_get_pt_different_unit(self, setup):  # pylint: disable=unused-argument
        """
        Tenta acessar um plano de trabalho de uma unidade diferente, à
        qual o usuário não tem acesso.
        """
        response = self.client.get(
            "/organizacao/SIAPE/3"  # Sem autorização nesta unidade
            f"/plano_trabalho/{self.input_pt['id_plano_trabalho']}",
            headers=self.header_usr_2,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_pt_different_unit_admin(self, setup):  # pylint: disable=unused-argument
        """
        Tenta acessar um plano de trabalho de uma unidade diferente, mas
        com um usuário com permissão de admin.
        """
        response = self.client.get(
            f"/organizacao/SIAPE/3"  # Unidade diferente
            f"/plano_trabalho/{self.input_pt['id_plano_trabalho']}",
            headers=self.header_admin,
        )

        # Inclui os campos de resposta do json que não estavam no template
        self.input_pt["status"] = 3
        self.input_pt["cod_unidade_executora"] = 3
        self.input_pt["carga_horaria_disponivel"] = self.input_pt["carga_horaria_disponivel"]
        self.input_pt["avaliacao_registros_execucao"][0][
            "data_avaliacao_registros_execucao"
        ] = "2023-01-03"

        assert response.status_code == status.HTTP_200_OK
        assert_equal_plano_trabalho(response.json(), self.input_pt)
