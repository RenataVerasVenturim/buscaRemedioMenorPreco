"""Leitura do catalogo publico VTEX usado por varias farmacias."""

from urllib.parse import quote, urljoin

import requests

from farmacias.filtro import classificar_tipo, produto_compativel, reais_para_centavos
from farmacias.http import obter, postar_json


def url_busca(base, termo):
    termo_codificado = quote(termo)
    return (
        f"{base.rstrip('/')}/api/catalog_system/pub/products/search"
        f"?ft={termo_codificado}&_from=0&_to=19"
    )


def _melhor_oferta(item):
    melhor = None
    item_id = item.get("itemId") or item.get("id")
    for seller in item.get("sellers") or []:
        oferta = seller.get("commertialOffer") or {}
        preco = oferta.get("Price")
        if preco is None:
            continue
        quantidade = oferta.get("AvailableQuantity") or 0
        disponivel = bool(oferta.get("IsAvailable")) and quantidade > 0 and preco > 0
        candidata = {
            "preco": preco,
            "quantidade": quantidade,
            "disponivel": disponivel,
            "vendedor": seller.get("sellerName") or "",
            "seller_id": seller.get("sellerId"),
            "item_id": item_id,
        }
        if melhor is None:
            melhor = candidata
            continue
        if disponivel and not melhor["disponivel"]:
            melhor = candidata
        elif disponivel == melhor["disponivel"] and preco < melhor["preco"]:
            melhor = candidata
    return melhor


def _calcular_frete(base, item_id, seller_id, quantidade, cep):
    url = urljoin(
        base.rstrip("/") + "/",
        "api/checkout/pub/orderForms/simulation?sc=1",
    )
    resposta = postar_json(
        url,
        {
            "items": [
                {
                    "id": str(item_id),
                    "quantity": int(quantidade),
                    "seller": str(seller_id),
                }
            ],
            "postalCode": cep,
            "country": "BRA",
        },
    )
    simulacao = resposta.json()
    if not isinstance(simulacao, dict):
        raise ValueError("A resposta de frete da VTEX não é válida.")

    logistics = simulacao.get("logisticsInfo")
    if not isinstance(logistics, list) or not logistics:
        raise ValueError("A VTEX não retornou opções de entrega para este CEP.")

    precos = []
    for entrega in logistics:
        if not isinstance(entrega, dict):
            continue
        for sla in entrega.get("slas") or []:
            if not isinstance(sla, dict):
                continue
            preco = sla.get("price")
            if (
                isinstance(preco, (int, float))
                and not isinstance(preco, bool)
                and preco >= 0
            ):
                precos.append(int(round(preco)))

    if not precos:
        raise ValueError("A VTEX não retornou preço de entrega para este CEP.")
    return min(precos)


def extrair_ofertas(produtos, farmacia, consulta, origem="catalogo", base=None):
    encontradas = []
    for produto in produtos:
        nome = produto.get("productName") or produto.get("productTitle") or ""
        marca = produto.get("brand") or ""
        if not produto_compativel(nome, consulta, marca):
            continue
        link = produto.get("link") or ""
        tipo = classificar_tipo(nome, marca)
        for item in produto.get("items") or []:
            nome_item = item.get("nameComplete") or item.get("name") or nome
            if not produto_compativel(nome_item, consulta, marca):
                continue
            oferta = _melhor_oferta(item)
            if not oferta or not oferta["preco"]:
                continue
            frete = None
            frete_confirmado = False
            frete_erro = None
            if consulta.cep:
                if not oferta["item_id"] or not oferta["seller_id"]:
                    frete_erro = "Catálogo sem SKU ou vendedor para cotar o frete."
                else:
                    try:
                        frete = _calcular_frete(
                            base,
                            oferta["item_id"],
                            oferta["seller_id"],
                            consulta.caixas,
                            consulta.cep,
                        )
                        frete_confirmado = True
                    except (ValueError, TypeError) as erro:
                        frete_erro = str(erro)
                    except requests.RequestException as erro:
                        frete_erro = f"Falha ao consultar o frete: {erro}"

            encontradas.append(
                {
                    "farmacia": farmacia,
                    "produto": nome_item,
                    "produto_tipo": tipo,
                    "url": link,
                    "preco_produtos": reais_para_centavos(oferta["preco"]),
                    "frete": frete,
                    "caixas": consulta.caixas,
                    "produto_confirmado": True,
                    "frete_confirmado": frete_confirmado,
                    "frete_erro": frete_erro,
                    "estoque_confirmado": bool(oferta["disponivel"]),
                    "origem": origem,
                    "laboratorio": marca,
                }
            )
    return encontradas


def pesquisar_vtex(farmacia, base, consulta):
    resposta = obter(url_busca(base, consulta.termo_busca), aceitar_json=True)
    produtos = resposta.json()
    if not isinstance(produtos, list):
        raise RuntimeError(f"{farmacia} não devolveu um catálogo reconhecível.")
    return extrair_ofertas(
        produtos,
        farmacia,
        consulta,
        origem="catalogo",
        base=base,
    )
