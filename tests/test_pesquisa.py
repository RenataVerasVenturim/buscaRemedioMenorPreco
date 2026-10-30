import json
from pathlib import Path

from farmacias.bula import extrair_ofertas as extrair_bula
from farmacias.farma22 import pesquisar as pesquisar_farma22
from farmacias.farmagerty import (
    _extrair_ofertas as extrair_farmagerty,
    _url_busca as url_busca_farmagerty,
    pesquisar as pesquisar_farmagerty,
)
from farmacias.filtro import Consulta, produto_compativel
from farmacias.vtex import extrair_ofertas as extrair_vtex
from services.comparador import ordenar_por_preco_produtos
from services.pesquisador import PesquisaIndisponivelError, pesquisar

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

CONSULTA = Consulta(
    principio_ativo="Ácido ursodesoxicólico",
    concentracao="300 mg",
    comprimidos=30,
    marcas_aceitas=["Ursacol", "Genérico", "Ranbaxy"],
)


def test_filtro_aceita_apresentacao_correta():
    assert produto_compativel(
        "Ácido Ursodesoxicólico 300mg 30 Comprimidos Genérico Ranbaxy",
        CONSULTA,
        "Ranbaxy",
    )
    assert produto_compativel("Ursacol 300mg 30 Comprimidos", CONSULTA)
    assert produto_compativel(
        "Ácido Ursodesoxicólico 300mg 30 comprimidos Ranbaxy",
        CONSULTA,
    )
    assert produto_compativel(
        "Ácido Ursodesoxicólico 300mg com 30 comprimidos - Ranbaxy Genérico",
        CONSULTA,
    )


def test_farmagerty_encontra_produto_ranbaxy():
    html = """
    <div class="product">
      <a class="product-info"
         href="https://www.farmagerty.com.br/acido-ursodesoxicolico-300mg-c30-comp-ranbaxy">
        <div class="product-name">
          Ácido Ursodesoxicólico 300mg 30 comprimidos Ranbaxy
        </div>
        <div class="product-price">
          <span class="old-price">R$ 199,19</span>
          <span class="current-price">R$ 108,40</span>
          <span class="preco-avista">R$ 105,15</span>
          <span class="preco-parc2">R$ 36,13</span>
        </div>
      </a>
    </div>
    """

    ofertas = extrair_farmagerty(html, CONSULTA)

    assert len(ofertas) == 1
    assert ofertas[0]["farmacia"] == "Farmagerty"
    assert ofertas[0]["produto"] == (
        "Ácido Ursodesoxicólico 300mg 30 comprimidos Ranbaxy"
    )
    assert ofertas[0]["preco_produtos"] == 10840


def test_farmagerty_usa_endpoint_de_busca_da_tray():
    assert url_busca_farmagerty(CONSULTA) == (
        "https://www.farmagerty.com.br/loja/busca.php"
        "?loja=1189842&palavra_busca=%C3%81cido+ursodesoxic%C3%B3lico+300mg"
    )


def test_pesquisar_farmagerty_usa_o_endpoint_e_propaga_erros(monkeypatch):
    chamadas = []

    def obter(url):
        chamadas.append(url)
        raise RuntimeError("Falha de conexão")

    monkeypatch.setattr("farmacias.farmagerty.obter", obter)

    with pytest.raises(RuntimeError, match="Falha de conexão"):
        pesquisar_farmagerty(CONSULTA)

    assert chamadas == [url_busca_farmagerty(CONSULTA)]


def test_filtro_rejeita_dose_errada_e_falso_positivo():
    assert not produto_compativel(
        "Ácido Ursodesoxicólico 150mg 30 Comprimidos",
        CONSULTA,
    )
    assert not produto_compativel("Ácido Alfa Lipóico 300mg 60 cápsulas", CONSULTA)
    assert not produto_compativel(
        "Ácido Ursodesoxicólico 300mg 60 Comprimidos",
        CONSULTA,
    )


def test_parser_vtex_ignora_produtos_incompativeis():
    produtos = json.loads((FIXTURES / "vtex_amostra.json").read_text(encoding="utf-8"))
    ofertas = extrair_vtex(produtos, "Pague Menos", CONSULTA)
    assert len(ofertas) == 1
    assert ofertas[0]["preco_produtos"] == 13399
    assert ofertas[0]["estoque_confirmado"] is True


def test_farma22_usa_catalogo_vtex(monkeypatch):
    chamadas = []

    def pesquisar_vtex(farmacia, base, consulta):
        chamadas.append((farmacia, base, consulta))
        return []

    monkeypatch.setattr("farmacias.farma22.pesquisar_vtex", pesquisar_vtex)

    assert pesquisar_farma22(CONSULTA) == []
    assert chamadas == [
        ("Farma 22", "https://www.farma22.com.br", CONSULTA)
    ]


def test_parser_vtex_aceita_generico_ranbaxy_da_farma22():
    produtos = [
        {
            "productName": (
                "Acido Ursodesoxicolico 300mg 30 comprimidos "
                "Genérico Ranbaxi"
            ),
            "brand": "RANBAXY",
            "link": (
                "https://www.farma22.com.br/"
                "acido-ursodesoxicolico-300mg-30-comprimidos-generico-ranbaxi/p"
            ),
            "items": [
                {
                    "itemId": "480580286",
                    "nameComplete": (
                        "Acido Ursodesoxicolico 300mg 30 comprimidos "
                        "Genérico Ranbaxi"
                    ),
                    "sellers": [
                        {
                            "sellerId": "1",
                            "commertialOffer": {
                                "Price": 99.9,
                                "IsAvailable": True,
                                "AvailableQuantity": 100,
                            },
                        }
                    ],
                }
            ],
        }
    ]

    ofertas = extrair_vtex(produtos, "Farma 22", CONSULTA)

    assert len(ofertas) == 1
    assert ofertas[0]["preco_produtos"] == 9990
    assert ofertas[0]["estoque_confirmado"] is True
    assert ofertas[0]["laboratorio"] == "RANBAXY"


def test_parser_vtex_cota_frete_com_cep_e_quantidade(monkeypatch):
    produtos = json.loads((FIXTURES / "vtex_amostra.json").read_text(encoding="utf-8"))
    consulta = Consulta(
        principio_ativo="Ácido ursodesoxicólico",
        concentracao="300 mg",
        comprimidos=30,
        caixas=3,
        marcas_aceitas=["Ursacol", "Genérico"],
        cep="24230-135",
    )
    chamadas = []

    class Resposta:
        def json(self):
            return {
                "logisticsInfo": [
                    {"slas": [{"price": 1290}, {"price": 0}]}
                ]
            }

    def postar_json(url, dados):
        chamadas.append((url, dados))
        return Resposta()

    monkeypatch.setattr("farmacias.vtex.postar_json", postar_json)
    ofertas = extrair_vtex(
        produtos,
        "Pague Menos",
        consulta,
        base="https://www.paguemenos.com.br",
    )

    assert len(ofertas) == 1
    assert ofertas[0]["frete"] == 0
    assert ofertas[0]["frete_confirmado"] is True
    assert ofertas[0]["caixas"] == 3
    assert chamadas[0][1] == {
        "items": [{"id": "sku-uds-300", "quantity": 3, "seller": "1"}],
        "postalCode": "24230135",
        "country": "BRA",
    }


def test_consulta_valida_cep():
    with pytest.raises(ValueError, match="CEP"):
        Consulta(principio_ativo="Medicamento", cep="12345")


def test_ranking_prioriza_totais_com_frete_confirmado():
    ofertas = [
        {
            "farmacia": "Frete desconhecido",
            "preco_produtos": 5000,
            "frete": None,
            "frete_confirmado": False,
            "caixas": 1,
        },
        {
            "farmacia": "Total confirmado",
            "preco_produtos": 6000,
            "frete": 500,
            "frete_confirmado": True,
            "caixas": 1,
        },
    ]

    ranking = ordenar_por_preco_produtos(ofertas)
    assert ranking[0]["farmacia"] == "Total confirmado"
    assert ranking[1]["farmacia"] == "Frete desconhecido"


def test_parser_bula_le_preco_atual():
    html = (FIXTURES / "bula_amostra.html").read_text(encoding="utf-8")
    ofertas = extrair_bula(html, CONSULTA)
    ranking = ordenar_por_preco_produtos(ofertas)
    assert ranking[0]["farmacia"] == "Farmácia Preço Popular"
    assert ranking[0]["preco_produtos"] == 11489
    assert ranking[1]["produto"].startswith("Ursacol")


def test_pesquisa_so_panvel_continua_indisponivel():
    with pytest.raises(PesquisaIndisponivelError):
        pesquisar("Ácido ursodesoxicólico", ["Panvel"])
