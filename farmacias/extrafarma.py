"""Fonte Extrafarma via catalogo publico VTEX."""

from farmacias.vtex import pesquisar_vtex

NOME = "Extrafarma"
STATUS = "ativo"
BASE = "https://www.extrafarma.com.br"


def pesquisar(consulta):
    return pesquisar_vtex(NOME, BASE, consulta)
