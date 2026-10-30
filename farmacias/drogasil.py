"""Fonte Drogasil. O site bloqueia consulta automatizada (Akamai)."""

NOME = "Drogasil"
STATUS = "bloqueada"
BASE = "https://www.drogasil.com.br"


def pesquisar(consulta):
    raise RuntimeError(
        "A Drogasil bloqueia consulta automatizada. "
        "Confira o preço no site e registre uma observação manual."
    )
