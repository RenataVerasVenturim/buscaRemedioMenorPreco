"""Fonte Panvel. O site bloqueia consulta automatizada (Akamai)."""

NOME = "Panvel"
STATUS = "bloqueada"
BASE = "https://www.panvel.com"


def pesquisar(consulta):
    raise RuntimeError(
        "A Panvel bloqueia consulta automatizada. "
        "Confira o preço no site e registre uma observação manual."
    )
