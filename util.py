"""Funções de utilidade comum.
"""

def sa_obj_to_dict(d: dict) -> dict:
    "Copia os valores do objeto SQL Alchemy para um dicionário."
    return {
        k:
            [
                sa_obj_to_dict(item)
                for item in v
            ] if isinstance(v, list) and v else v
        for k, v in d.__dict__.items()
        if not k.startswith("_")
    }

def merge_dicts(d1: dict, d2:dict) -> dict:
    "Atualiza d1 com os valores de d2."
    # os que estão em d1, atualizar com d2
    d = {
        k: merge_dicts(v, d2.get(k, {})) \
            if isinstance(v, dict) and v \
            else d2.get(k, v)
        for k, v in d1.items()
    }
    # os que estão em d2 mas não em d1, copiar de d2
    d.update({
        k: v
        for k, v in d2.items()
        if k not in d1.keys()
    })
    return d

def list_to_dict(l: list, id_attr: str) -> dict:
    "Transforma uma lista em dicionário, tomando o id como chave."
    return {
        entry.get(id_attr): {
            key: value
            for key, value in entry.items() if key != id_attr
        }
        for entry in l
    }

def dict_to_list(d: dict, id_attr: str) -> list:
    "Transforma um dicionário em lista, tomando o id como chave."
    return [
        merge_dicts(
            {
                id_attr: item_id
            },
            {
                key: value
                for key, value in prop.items()
            }
        )
        for item_id, prop in sorted(d.items())
    ]