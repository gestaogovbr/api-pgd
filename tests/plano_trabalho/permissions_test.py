import pytest
from httpx import Client
from fastapi import status

from .core_test import BasePTTest


class TestPlanoDeTrabalhoDiferenteUnidade(BasePTTest):
    """
    Testes para verificar o acesso a um plano de trabalho de uma unidade
    diferente.

    Esses testes verificam o comportamento do sistema quando um usuário
    tenta acessar ou criar um plano de trabalho de uma unidade diferente,
    tanto com um usuário sem permissão quanto com um usuário com
    permissão de administrador.
    """

    def test_get_pt_different_unit(
        self,
        header_usr_2: dict,
        example_pe_unidade_3,  # pylint: disable=unused-argument
        example_pt_unidade_3,  # pylint: disable=unused-argument
    ):
        """
        Tenta acessar um plano de trabalho de uma unidade diferente, à
        qual o usuário não tem acesso.
        """
        response = self.get_pt(
            id_plano_trabalho=self.input_pt["id_plano_trabalho"],
            cod_unidade_autorizadora=3,  # Unidade diferente
            header_usr=header_usr_2
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        detail_message = "Usuário não tem permissão na cod_unidade_autorizadora informada"
        assert detail_message in response.json().get("detail")

    def test_get_pt_different_unit_admin(
        self,
        header_admin: dict,
        example_pe_unidade_3,  # pylint: disable=unused-argument
        example_pt_unidade_3,  # pylint: disable=unused-argument
    ):
        """
        Tenta acessar um plano de trabalho de uma unidade diferente, mas
        com um usuário com permissão de admin.
        """
        # Obter o plano de trabalho de uma unidade diferente
        response = self.get_pt(
            self.input_pt["id_plano_trabalho"], 3, header_usr=header_admin
        )

        # Inclui os campos de resposta do json que não estavam no template
        input_pt = self.input_pt.copy()
        input_pt["status"] = 3
        input_pt["cod_unidade_executora"] = 3
        input_pt["carga_horaria_disponivel"] = input_pt[
            "carga_horaria_disponivel"
        ]
        input_pt["avaliacao_registros_execucao"][0][
            "data_avaliacao_registros_execucao"
        ] = "2023-01-03"

        assert response.status_code == status.HTTP_200_OK
        self.assert_equal_plano_trabalho(response.json(), input_pt)

def test_create_plano_trabalho_unidade_nao_permitida(self, header_usr_2):
    """Tenta criar um novo Plano de Trabalho do Participante em uma
    organização na qual ele não está autorizado.
    """
    # Criar o Plano de Trabalho em uma unidade diferente
    response = self.create_pt(
        self.input_pt, cod_unidade_autorizadora=3, header_usr=header_usr_2
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    detail_message = "Usuário não tem permissão na cod_unidade_autorizadora informada"
    assert detail_message in response.json().get("detail")

