"""Fonte Pague Menos via catalogo publico VTEX."""

from farmacias.vtex import pesquisar_vtex

NOME = "Pague Menos"
STATUS = "ativo"
BASE = "https://www.paguemenos.com.br"


def pesquisar(consulta):
    return pesquisar_vtex(NOME, BASE, consulta)
