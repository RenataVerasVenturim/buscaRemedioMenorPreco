import pytest

import database.database as database
from services.alertas import avaliar_desconto
from services.analise_estatistica import calcular_estatisticas
from services.comparador import comparar_ofertas
from services.frete import calcular_total
from services.pesquisador import PesquisaIndisponivelError, pesquisar


def test_frete_nao_trata_valor_desconhecido_como_zero():
    assert calcular_total(2500, None, False) is None
    assert calcular_total(2500, 0, True) == 2500
    assert calcular_total(2500, 500, True) == 3000


def test_comparador_exige_confirmacao_de_produto_frete_e_estoque():
    ofertas = [
        {
            "farmacia": "Panvel",
            "preco_produtos": 2500,
            "frete": 400,
            "produto_confirmado": 1,
            "frete_confirmado": 1,
            "estoque_confirmado": 1,
        },
        {
            "farmacia": "Drogasil",
            "preco_produtos": 2000,
            "frete": 0,
            "produto_confirmado": 1,
            "frete_confirmado": 1,
            "estoque_confirmado": 0,
        },
    ]

    resultado = comparar_ofertas(ofertas)

    assert [oferta["farmacia"] for oferta in resultado] == ["Panvel"]
    assert resultado[0]["preco_total"] == 2900


def test_estatisticas_e_alerta():
    estatisticas = calcular_estatisticas([1000, 2000, 3000])
    assert estatisticas["media"] == 2000
    assert estatisticas["mediana"] == 2000
    assert avaliar_desconto(1800, 2000, 10)["alerta"] is True
    assert avaliar_desconto(1900, 2000, 10)["alerta"] is False


def test_nao_pesquisa_sem_conector_real():
    with pytest.raises(PesquisaIndisponivelError):
        pesquisar("medicamento", ["Panvel"])


def test_registra_oferta_manual_no_banco(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "historico.db")
    database.inicializar_banco()

    database.registrar_oferta_manual(
        medicamento="Medicamento de teste",
        farmacia="Panvel",
        produto="Produto 300 mg",
        produto_tipo="Marca",
        url=None,
        preco_produtos=2500,
        frete=500,
        caixas=1,
        produto_confirmado=True,
        frete_confirmado=True,
        estoque_confirmado=True,
    )

    historico = database.obter_historico("Medicamento de teste")
    assert len(historico) == 1
    assert historico[0]["preco_total"] == 3000
    assert historico[0]["produto_confirmado"] == 1


def test_persiste_frete_calculado_na_pesquisa_automatica(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "historico.db")
    database.inicializar_banco()

    database.registrar_pesquisa_automatica(
        "Medicamento de teste",
        [
            {
                "farmacia": "Pague Menos",
                "produto": "Produto 300 mg",
                "preco_produtos": 2500,
                "frete": 400,
                "frete_confirmado": True,
                "produto_confirmado": True,
                "estoque_confirmado": True,
            }
        ],
        caixas=2,
    )

    historico = database.obter_historico("Medicamento de teste")
    assert len(historico) == 1
    assert historico[0]["preco_produtos"] == 5000
    assert historico[0]["frete"] == 400
    assert historico[0]["preco_total"] == 5400
    assert historico[0]["frete_confirmado"] == 1
