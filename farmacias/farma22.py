"""Fonte Farma 22 via catalogo publico VTEX."""

from farmacias.vtex import pesquisar_vtex

NOME = "Farma 22"
STATUS = "ativo"
BASE = "https://www.farma22.com.br"


def pesquisar(consulta):
    return pesquisar_vtex(NOME, BASE, consulta)
