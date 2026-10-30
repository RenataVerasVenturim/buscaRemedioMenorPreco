"""Fonte Drogal via catalogo publico VTEX."""

from farmacias.vtex import pesquisar_vtex

NOME = "Drogal"
STATUS = "ativo"
BASE = "https://www.drogal.com.br"


def pesquisar(consulta):
    return pesquisar_vtex(NOME, BASE, consulta)
