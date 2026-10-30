"""Fonte Drogaria Sao Paulo via catalogo publico VTEX."""

from farmacias.vtex import pesquisar_vtex

NOME = "Drogaria São Paulo"
STATUS = "ativo"
BASE = "https://www.drogariasaopaulo.com.br"


def pesquisar(consulta):
    return pesquisar_vtex(NOME, BASE, consulta)
