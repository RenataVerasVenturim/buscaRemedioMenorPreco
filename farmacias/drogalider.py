"""Drogalider: site com desafio de segurança e sem suporte automatizado."""

from farmacias.filtro import Consulta

NOME = "Drogalider"
STATUS = "bloqueada"
BASE = "https://www.drogalider.com.br"


def pesquisar(consulta: Consulta):
    raise RuntimeError(
        "A Drogalider bloqueia consultas automáticas. "
        "Registre a oferta manualmente para incluir o frete e o estoque."
    )
