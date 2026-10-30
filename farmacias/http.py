"""Cliente HTTP compartilhado para consultas publicas de catalogo."""

import requests

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

TIMEOUT = 20


def obter(url, *, aceitar_json=False):
    cabecalhos = dict(CABECALHOS)
    if aceitar_json:
        cabecalhos["Accept"] = "application/json,text/plain,*/*;q=0.8"
    resposta = requests.get(url, headers=cabecalhos, timeout=TIMEOUT)
    resposta.raise_for_status()
    return resposta


def postar_json(url, dados):
    cabecalhos = dict(CABECALHOS)
    cabecalhos["Accept"] = "application/json,text/plain,*/*;q=0.8"
    cabecalhos["Content-Type"] = "application/json"
    resposta = requests.post(
        url,
        headers=cabecalhos,
        json=dados,
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    return resposta
