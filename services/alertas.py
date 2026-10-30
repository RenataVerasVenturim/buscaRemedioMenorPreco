"""Avalia alertas de preco contra uma referencia historica."""


def avaliar_desconto(preco_atual, media_historica, desconto_percentual):
    if preco_atual < 0 or media_historica < 0:
        raise ValueError("Os preços não podem ser negativos.")
    if not 0 <= desconto_percentual <= 100:
        raise ValueError("O desconto deve estar entre 0 e 100%.")
    if media_historica == 0:
        return {
            "alerta": False,
            "desconto_percentual": None,
            "preco_limite": None,
        }

    desconto = (media_historica - preco_atual) / media_historica * 100
    preco_limite = media_historica * (1 - desconto_percentual / 100)
    return {
        "alerta": preco_atual <= preco_limite,
        "desconto_percentual": desconto,
        "preco_limite": preco_limite,
    }