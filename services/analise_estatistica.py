"""Calcula estatisticas basicas de precos expressos em centavos."""

from statistics import mean, median


def calcular_estatisticas(precos):
    valores = list(precos)
    if not valores:
        return None
    if any(isinstance(valor, bool) or valor < 0 for valor in valores):
        raise ValueError("Os preços devem ser valores não negativos em centavos.")
    return {
        "observacoes": len(valores),
        "media": mean(valores),
        "mediana": median(valores),
        "minimo": min(valores),
        "maximo": max(valores),
    }