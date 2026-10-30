"""Entrada para pesquisa agendada nas fontes ativas."""

from farmacias.filtro import Consulta
from services.pesquisador import pesquisar


def executar_pesquisa(medicamento, farmacias=None, consulta=None):
    if consulta is None:
        consulta = Consulta(principio_ativo=medicamento)
    return pesquisar(medicamento, farmacias, consulta=consulta)
