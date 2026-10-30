"""Fonte Drogaria Pacheco via catalogo publico VTEX."""

from farmacias.vtex import pesquisar_vtex

NOME = "Drogaria Pacheco"
STATUS = "ativo"
BASE = "https://www.drogariaspacheco.com.br"


def pesquisar(consulta):
    return pesquisar_vtex(NOME, BASE, consulta)
