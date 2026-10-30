"""Farmagerty: busca por página de catálogo da loja Tray."""

from urllib.parse import urlencode

from bs4 import BeautifulSoup

from farmacias.filtro import classificar_tipo, produto_compativel, reais_para_centavos
from farmacias.http import obter

NOME = "Farmagerty"
STATUS = "ativo"
BASE = "https://www.farmagerty.com.br"
LOJA = "1189842"


def _url_busca(consulta):
    parametros = urlencode(
        {
            "loja": LOJA,
            "palavra_busca": consulta.termo_busca,
        }
    )
    return f"{BASE}/loja/busca.php?{parametros}"


def _extrair_ofertas(html, consulta):
    soup = BeautifulSoup(html, "html.parser")
    encontradas = []
    vistos = set()
    links = soup.select("a.product-info[href]") or soup.select("a[href]")
    for link in links:
        href = link.get("href", "")
        nome = link.select_one(".product-name")
        texto = " ".join(
            (nome or link).get_text(" ", strip=True).split()
        )
        if not href or not texto:
            continue
        href = href.strip()
        if href.startswith("/"):
            href = BASE + href
        if href in vistos or not href.startswith("http"):
            continue
        vistos.add(href)
        if not produto_compativel(texto, consulta):
            continue
        preco = None
        valor_atual = link.select_one(".current-price")
        valor_pix = link.select_one(".preco-avista")
        if valor_atual:
            preco = reais_para_centavos(valor_atual.get_text(" ", strip=True))
        elif valor_pix:
            preco = reais_para_centavos(valor_pix.get_text(" ", strip=True))
        else:
            bloco = link.find_parent()
            if bloco:
                texto_bloco = " ".join(bloco.get_text(" ", strip=True).split())
                if "R$" in texto_bloco:
                    valor = texto_bloco[texto_bloco.rfind("R$"):]
                    preco = reais_para_centavos(valor)
        if preco is None:
            continue
        encontradas.append(
            {
                "farmacia": NOME,
                "produto": texto,
                "produto_tipo": classificar_tipo(texto),
                "url": href,
                "preco_produtos": preco,
                "frete": None,
                "caixas": consulta.caixas,
                "produto_confirmado": True,
                "frete_confirmado": False,
                "estoque_confirmado": False,
                "origem": "catalogo",
                "laboratorio": "",
            }
        )
    return encontradas


def pesquisar(consulta):
    resposta = obter(_url_busca(consulta))
    return _extrair_ofertas(resposta.text, consulta)
