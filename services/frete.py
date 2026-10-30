"""Calcula totais sem confundir frete estimado com frete confirmado."""


def calcular_total(preco_produtos, frete, frete_confirmado):
    """Retorna o total em centavos; sem frete confirmado, o total e desconhecido."""
    if isinstance(preco_produtos, bool) or preco_produtos < 0:
        raise ValueError("O preço dos produtos não pode ser negativo.")
    if frete is not None and (isinstance(frete, bool) or frete < 0):
        raise ValueError("O frete não pode ser negativo.")
    if frete_confirmado and frete is None:
        raise ValueError("Frete confirmado exige um valor informado.")
    return preco_produtos + frete if frete_confirmado else None