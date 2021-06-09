"""
Testes do módulo util.
"""

import util

from tests.atividade_test import atividades_dict

# Unit tests

def test_merge_dicts(input_pt: dict):
    """Testa a mesclagem de dicionários.
    """
    input1 = input_pt.copy()
    input2 = input_pt.copy()

    del input1["atividades"][0]["qtde_entregas"]
    del input2["atividades"][0]["avaliacao"]

    assert util.merge_dicts(input1, input2) == input_pt

def test_list_to_dict(input_pt: dict):
    """Testa a transformação de lista em dicionário.
    """
    atividades = util.list_to_dict(input_pt["atividades"], "id_atividade")

    assert atividades == atividades_dict

def test_dict_to_list(input_pt: dict):
    """Testa a transformação de lista em dicionário.
    """
    atividades = util.dict_to_list(atividades_dict, "id_atividade")

    assert atividades == input_pt["atividades"]