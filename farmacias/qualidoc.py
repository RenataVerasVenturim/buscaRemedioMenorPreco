"""Qualidoc: consulta de busca em modo best-effort."""

from urllib.parse import quote

from bs4 import BeautifulSoup

from farmacias.filtro import classificar_tipo, produto_compativel, reais_para_centavos
from farmacias.http import obter

NOME = "Qualidoc"
STATUS = "ativo"
BASE = "https://www.qualidoc.com.br"


def _url_busca(consulta):
    termo = quote(consulta.termo_busca)
    return f"{BASE}/search/?products%5Bquery%5D={termo}"


def _extrair_ofertas(html, consulta):
    soup = BeautifulSoup(html, "html.parser")
    encontradas = []
    visto = set()
    for link in soup.select("a[href]"):
        href = link.get("href", "")
        texto = " ".join(link.get_text(" ", strip=True).split())
        if not href or not texto:
            continue
        href = href.strip()
        if href.startswith("/"):
            href = BASE + href
        if href in visto or not href.startswith("http"):
            continue
        visto.add(href)
        if not produto_compativel(texto, consulta):
            continue
        preco = None
        bloco = link.find_parent()
        if bloco:
            texto_bloco = " ".join(bloco.get_text(" ", strip=True).split())
            if "R$" in texto_bloco:
                valor = texto_bloco[texto_bloco.rfind("R$"):]
                preco = reais_para_centavos(valor)
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
    return [oferta for oferta in encontradas if oferta["preco_produtos"] is not None]


def pesquisar(consulta):
    try:
        resposta = obter(_url_busca(consulta))
        return _extrair_ofertas(resposta.text, consulta)
    except Exception:
        return []
