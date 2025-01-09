"""
Testes relacionados às funcionalidades básicas da limpeza de migração
"""

from typing import Optional

import pytest
from fastapi import status
from httpx import Client, Response

# grupos de campos opcionais e obrigatórios a testar

FIELDS_MIGRACAO = {
    "optional": tuple(),  # nenhum campo é opcional
    "mandatory": (
        ["origem_unidade"],
        ["cod_unidade_autorizadora"]
    ),
}


# Classe base de testes

class BaseMigracaoTest:
    """Classe base para testes da limpeza de migração."""

    # pylint: disable=too-many-arguments
    @pytest.fixture(autouse=True)
    def setup(
            self,
            truncate_participantes,  # pylint: disable=unused-argument
            truncate_pe,  # pylint: disable=unused-argument
            truncate_pt,  # pylint: disable=unused-argument
            example_pe,  # pylint: disable=unused-argument
            example_part,  # pylint: disable=unused-argument
            example_pt,  # pylint: disable=unused-argument
            input_pt: dict,
            user1_credentials: dict,
            header_usr_1: dict,
            header_usr_2: dict,
            client: Client,
    ):
        """Configurar o ambiente de teste.

        Args:
            truncate_participantes (callable): Fixture para truncar a tabela de
                Participantes.
            truncate_pe (callable): Fixture para truncar a tabela de
                Planos de Entrega.
            truncate_pt (callable): Fixture para truncar a tabela de
                Planos de Trabalho.
            example_pe (callable): Fixture que cria exemplo de PE.
            input_pt (dict): Dados usados para ciar um PT
            user1_credentials (dict): Credenciais do usuário 1.
            header_usr_1 (dict): Cabeçalhos HTTP para o usuário 1.
            header_usr_2 (dict): Cabeçalhos HTTP para o usuário 2.
            client (Client): Uma instância do cliente HTTPX.
        """
        # pylint: disable=attribute-defined-outside-init
        self.input_pt = input_pt
        self.user1_credentials = user1_credentials
        self.header_usr_1 = header_usr_1
        self.header_usr_2 = header_usr_2
        self.client = client

    def delete_migracao(
            self,
            cod_unidade_autorizadora: int,
            origem_unidade: Optional[str] = "SIAPE",
            header_usr: Optional[dict] = None,
    ) -> Response:
        """Executa a limpeza de migração

        Args:
            cod_unidade_autorizadora (int): O ID da unidade autorizadora.
            origem_unidade (str): origem do código da unidade.
            header_usr (dict): Cabeçalhos HTTP para o usuário.

        Returns:
            httpx.Response: A resposta da API.
        """
        if header_usr is None:
            header_usr = self.header_usr_1
        response = self.client.delete(
            (
                f"/organizacao/{origem_unidade}/{cod_unidade_autorizadora}"
                f"/limpar-migracao"
            ),
            headers=header_usr,
        )
        return response


class TestDeletarMigracao(BaseMigracaoTest):
    """Testes para exclusão da migração."""

    def test_delete_migracao_success(self, example_pt, example_pe, example_part):  # pylint: disable=unused-argument
        response = self.delete_migracao(self.input_pt["cod_unidade_autorizadora"])
        assert response.status_code == status.HTTP_204_NO_CONTENT
