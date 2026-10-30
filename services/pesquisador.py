"""Orquestra a busca de precos nas fontes cadastradas."""

from farmacias.filtro import Consulta
from farmacias.outras import FARMACIAS


class PesquisaIndisponivelError(RuntimeError):
    """Nenhuma fonte conseguiu devolver ofertas."""


def listar_fontes():
    return [
        {"nome": farmacia["nome"], "status": farmacia["status"]}
        for farmacia in FARMACIAS
    ]


def _fontes_escolhidas(farmacias):
    catalogo = {farmacia["nome"]: farmacia for farmacia in FARMACIAS}
    if not farmacias:
        return list(FARMACIAS)
    desconhecidas = set(farmacias) - set(catalogo)
    if desconhecidas:
        raise ValueError(
            "Farmácias não cadastradas: " + ", ".join(sorted(desconhecidas))
        )
    return [catalogo[nome] for nome in farmacias]


def pesquisar(medicamento, farmacias=None, consulta=None):
    if consulta is None:
        if not str(medicamento or "").strip():
            raise ValueError("Informe o medicamento antes de pesquisar.")
        consulta = Consulta(principio_ativo=medicamento.strip())
    elif not consulta.principio_ativo.strip():
        raise ValueError("Informe o medicamento antes de pesquisar.")

    fontes = _fontes_escolhidas(farmacias)
    ofertas = []
    resultados_fontes = []
    for fonte in fontes:
        try:
            encontradas = fonte["pesquisar"](consulta) or []
            ofertas.extend(encontradas)
            resultados_fontes.append(
                {
                    "nome": fonte["nome"],
                    "status": "ok" if encontradas else "sem_ofertas",
                    "quantidade": len(encontradas),
                    "erro": None,
                }
            )
        except Exception as exc:
            resultados_fontes.append(
                {
                    "nome": fonte["nome"],
                    "status": "erro",
                    "quantidade": 0,
                    "erro": str(exc),
                }
            )

    if not ofertas and all(item["status"] == "erro" for item in resultados_fontes):
        raise PesquisaIndisponivelError(
            "Nenhuma farmácia devolveu preço agora. "
            "Tente de novo ou registre uma observação manual."
        )

    return {
        "consulta": consulta,
        "ofertas": ofertas,
        "fontes": resultados_fontes,
    }
