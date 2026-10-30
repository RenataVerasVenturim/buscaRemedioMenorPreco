"""Agregador publico Bula.com.br, com precos de varias farmacias."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from farmacias.filtro import (
    classificar_tipo,
    produto_compativel,
    reais_para_centavos,
    slugify,
)
from farmacias.http import obter

NOME = "Bula"
STATUS = "ativo"
BASE = "https://bula.com.br"


def url_precos(consulta):
    principio = slugify(consulta.principio_ativo)
    dose = f"{consulta.dose_mg}mg"
    return f"{BASE}/precos/{principio}/{dose}"


def _preco_oferta(bloco_preco):
    if bloco_preco is None:
        return None
    atual = bloco_preco.find("span", attrs={"style": lambda valor: valor and "font-weight:700" in valor})
    texto = atual.get_text(" ", strip=True) if atual else bloco_preco.get_text(" ", strip=True)
    if "R$" not in texto:
        return None
    trecho = texto[texto.rfind("R$") :]
    return reais_para_centavos(trecho)


def extrair_ofertas(html, consulta):
    soup = BeautifulSoup(html, "html.parser")
    encontradas = []
    for artigo in soup.select("article.op-caixa"):
        titulo = artigo.select_one(".op-caixa-nome")
        if titulo is None:
            continue
        produto = titulo.get_text(" ", strip=True)
        laboratorio = ""
        lab = artigo.select_one(".op-caixa-lab")
        if lab:
            laboratorio = lab.get_text(" ", strip=True)
        if not produto_compativel(produto, consulta, laboratorio):
            continue
        tipo = classificar_tipo(produto, laboratorio)
        for loja in artigo.select("li.op-loja"):
            nome_loja = loja.select_one(".op-loja-titulo")
            if nome_loja is None:
                continue
            farmacia = nome_loja.get_text(" ", strip=True)
            preco = _preco_oferta(loja.select_one(".op-preco"))
            if not preco:
                continue
            botao = loja.select_one("a.op-botao")
            url = urljoin(BASE + "/", botao.get("href", "")) if botao else BASE
            encontradas.append(
                {
                    "farmacia": farmacia,
                    "produto": produto,
                    "produto_tipo": tipo,
                    "url": url,
                    "preco_produtos": preco,
                    "frete": None,
                    "caixas": consulta.caixas,
                    "produto_confirmado": True,
                    "frete_confirmado": False,
                    "frete_erro": (
                        "O agregador não fornece SKU/vendedor para cotar o frete."
                        if consulta.cep
                        else None
                    ),
                    "estoque_confirmado": False,
                    "origem": "agregador",
                    "laboratorio": laboratorio,
                }
            )
    return encontradas


def pesquisar(consulta):
    resposta = obter(url_precos(consulta))
    return extrair_ofertas(resposta.text, consulta)
