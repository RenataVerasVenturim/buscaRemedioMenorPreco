def _total_com_frete(oferta):
    """Retorna o total confirmado somente quando o frete for conhecido e confirmado."""
    preco_produtos = oferta.get("preco_produtos")
    if preco_produtos is None:
        return None

    frete = oferta.get("frete")
    if frete is None or not oferta.get("frete_confirmado"):
        return None

    return preco_produtos * oferta.get("caixas", 1) + frete


def ordenar_ofertas(ofertas):
    """
    Recebe uma lista de ofertas e retorna
    somente as ofertas válidas, ordenadas
    pelo menor preço total.
    """

    validas = [
        oferta
        for oferta in ofertas
        if oferta.elegivel
    ]

    return sorted(
        validas,
        key=lambda oferta: oferta.preco_total
    )


def comparar_ofertas(ofertas):
    """Ordena dicionarios de historico com produto, frete e estoque confirmados."""
    validas = []
    for oferta in ofertas:
        if not (
            oferta.get("produto_confirmado")
            and oferta.get("frete_confirmado")
            and oferta.get("estoque_confirmado")
        ):
            continue
        preco_produtos = oferta.get("preco_produtos")
        frete = oferta.get("frete")
        if preco_produtos is None or frete is None:
            continue
        item = dict(oferta)
        item["preco_total"] = preco_produtos + frete
        validas.append(item)
    return sorted(validas, key=lambda oferta: oferta["preco_total"])


def ordenar_por_preco_produtos(ofertas):
    """Ranking da busca ao vivo, considerando frete quando ele for confirmado."""
    validas = [
        oferta
        for oferta in ofertas
        if oferta.get("preco_produtos") is not None
    ]
    return sorted(
        validas,
        key=lambda oferta: (
            _total_com_frete(oferta) is None,
            _total_com_frete(oferta)
            if _total_com_frete(oferta) is not None
            else oferta["preco_produtos"] * oferta.get("caixas", 1),
        ),
    )


def formatar_moeda(valor_centavos):
    if valor_centavos is None:
        return "Não informado"

    valor = valor_centavos / 100

    return f"R$ {valor:,.2f}".replace(
        ",", "X"
    ).replace(".", ",").replace("X", ".")
