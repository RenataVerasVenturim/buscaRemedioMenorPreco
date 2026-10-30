"""Registro das fontes de preco da primeira fase e das farmacias ativas."""

from farmacias import (
    bula,
    drogal,
    drogalider,
    drogaria_pacheco,
    drogaria_sao_paulo,
    drogasil,
    extrafarma,
    farma22,
    farmagerty,
    pague_menos,
    panvel,
    qualidoc,
)

FARMACIAS = (
    {
        "nome": panvel.NOME,
        "status": panvel.STATUS,
        "pesquisar": panvel.pesquisar,
    },
    {
        "nome": drogasil.NOME,
        "status": drogasil.STATUS,
        "pesquisar": drogasil.pesquisar,
    },
    {
        "nome": pague_menos.NOME,
        "status": pague_menos.STATUS,
        "pesquisar": pague_menos.pesquisar,
    },
    {
        "nome": extrafarma.NOME,
        "status": extrafarma.STATUS,
        "pesquisar": extrafarma.pesquisar,
    },
    {
        "nome": drogal.NOME,
        "status": drogal.STATUS,
        "pesquisar": drogal.pesquisar,
    },
    {
        "nome": drogaria_sao_paulo.NOME,
        "status": drogaria_sao_paulo.STATUS,
        "pesquisar": drogaria_sao_paulo.pesquisar,
    },
    {
        "nome": drogaria_pacheco.NOME,
        "status": drogaria_pacheco.STATUS,
        "pesquisar": drogaria_pacheco.pesquisar,
    },
    {
        "nome": farmagerty.NOME,
        "status": farmagerty.STATUS,
        "pesquisar": farmagerty.pesquisar,
    },
    {
        "nome": farma22.NOME,
        "status": farma22.STATUS,
        "pesquisar": farma22.pesquisar,
    },
    {
        "nome": qualidoc.NOME,
        "status": qualidoc.STATUS,
        "pesquisar": qualidoc.pesquisar,
    },
    {
        "nome": drogalider.NOME,
        "status": drogalider.STATUS,
        "pesquisar": drogalider.pesquisar,
    },
    {
        "nome": bula.NOME,
        "status": bula.STATUS,
        "pesquisar": bula.pesquisar,
    },
)
