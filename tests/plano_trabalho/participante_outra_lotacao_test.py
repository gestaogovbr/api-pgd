"""
Testes relacionados à vinculação do Plano de Trabalho a um Participante
que tem um cod_unidade_lotacao diferente do seu cod_unidade_executora.
"""

from fastapi import status

from util import assert_error_message

from .core_test import BasePTTest

class TestCreatePlanoTrabalhoParticipanteOutraUnidade(BasePTTest):
    """Testes para verificar a criação de um Plano de Trabalho
    vinculado a um Participante, onde o cod_unidade_executora difere
    do cod_unidade_lotacao.

    Segundo regra de negócio, um Participante pode ser lotado em uma
    unidade e executar um Plano de Trabalho em outra unidade.
    """
    def test_create_plano_trabalho_participante_outra_unidade(self):
        """Cria um Participante, e então cria um Plano de Trabalho
        vinculado a ele em outra unidade. Usa cod_unidade_lotacao
        diferente do cod_unidade_executora. Verifica se o Plano de Trabalho
        criado possui os dados informados para sua criação.
        """
        input_pt = self.input_pt.copy()
        # cod_unidade_lotacao do Participante criado pela fixture example_part
        # é 99
        # cod_unidade_executora original do input_part é 99
        input_pt['cod_unidade_executora'] = 101

        # cria o Plano de Trabalho
        response = self.put_plano_trabalho(
            input_pt=input_pt,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        self.assert_equal_plano_trabalho(response_data, input_pt)
        # verifica se a resposta veio com o cod_unidade_executora esperado
        assert response_data['cod_unidade_executora'] == 101

        # Consulta API para conferir se a criação foi persistida
        response = self.get_plano_trabalho(
            self.input_pt["id_plano_trabalho"],
            self.input_pt["cod_unidade_autorizadora"],
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        # verifica se os dados gravados são iguais aos informados
        self.assert_equal_plano_trabalho(response_data, input_pt)
        # verifica o cod_unidade_executora
        assert response_data['cod_unidade_executora'] == 101
