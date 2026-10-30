from farmacias.base import Oferta
from services.comparador import (
    ordenar_ofertas,
    formatar_moeda
)


def criar_oferta(farmacia, preco, frete):
    return Oferta(
        farmacia=farmacia,
        produto="Ácido ursodesoxicólico",
        produto_tipo="generico",
        concentracao="300mg",
        comprimidos=30,
        caixas=3,
        preco_produtos=preco,
        frete=frete,
        url="https://exemplo.com/produto",
        frete_confirmado=True,
        estoque_confirmado=True
    )


def test_ordena_pelo_menor_preco():
    ofertas = [
        criar_oferta("Farmácia A", 18000, 1800),
        criar_oferta("Farmácia B", 17400, 3200),
        criar_oferta("Farmácia C", 18900, 0)
    ]

    resultado = ordenar_ofertas(ofertas)

    assert resultado[0].farmacia == "Farmácia C"
    assert resultado[0].preco_total == 18900


def test_rejeita_frete_nao_confirmado():
    oferta = criar_oferta(
        "Farmácia A", 18000, 1500
    )

    oferta.frete_confirmado = False

    resultado = ordenar_ofertas([oferta])

    assert len(resultado) == 0


def test_formata_moeda():
    assert formatar_moeda(18990) == "R$ 189,90"