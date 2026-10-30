"""Interface Streamlit do comparador de medicamentos."""

from decimal import Decimal

import pandas as pd
import streamlit as st

from database.database import (
    inicializar_banco,
    obter_historico,
    registrar_oferta_manual,
    registrar_pesquisa_automatica,
)
from farmacias.filtro import Consulta
from farmacias.outras import FARMACIAS
from services.comparador import (
    comparar_ofertas,
    formatar_moeda,
    ordenar_por_preco_produtos,
)
from services.pesquisador import PesquisaIndisponivelError, pesquisar

st.set_page_config(
    page_title="Comparador de Medicamentos",
    page_icon="💊",
    layout="wide",
)

inicializar_banco()

st.title("💊 Ácido ursodesoxicólico 300 mg")
st.caption(
    "Busca preços de caixa com 30 comprimidos em farmácias online. "
    "O frete é cotado para o CEP informado quando a farmácia permite "
    "simulação automática; caso contrário, registre-o manualmente."
)

with st.sidebar:
    st.header("Medicamento e monitoramento")
    principio_ativo = st.text_input(
        "Princípio ativo",
        value="Ácido ursodesoxicólico",
    ).strip()
    concentracao = st.text_input("Concentração", value="300 mg").strip()
    comprimidos = st.number_input(
        "Comprimidos por caixa",
        min_value=1,
        value=30,
        step=1,
    )
    caixas = st.number_input(
        "Caixas desejadas",
        min_value=1,
        value=3,
        step=1,
    )
    marcas_aceitas = st.text_input(
        "Marcas aceitas (separadas por vírgula)",
        value="Ursacol, Genérico, Prour, Ranbaxy",
    )
    cep = st.text_input("CEP de entrega", value="24230135").strip()
    intervalo_dias = st.number_input(
        "Intervalo de monitoramento (dias)",
        min_value=1,
        value=90,
        step=1,
    )
    desconto_alerta = st.number_input(
        "Desconto para alerta (%)",
        min_value=0.0,
        max_value=100.0,
        value=10.0,
        step=1.0,
    )

marcas = [
    marca.strip()
    for marca in marcas_aceitas.split(",")
    if marca.strip()
]

st.subheader("Fontes de preço")
source_columns = st.columns(4)
for indice, farmacia in enumerate(FARMACIAS):
    with source_columns[indice % 4]:
        st.markdown(f"**{farmacia['nome']}**")
        if farmacia["status"] == "ativo":
            st.success("Busca automática")
        else:
            st.warning("Site bloqueia robô — use observação manual")

consultar = st.button("Buscar preços agora", type="primary")

if consultar:
    with st.spinner("Consultando farmácias e o agregador Bula..."):
        try:
            consulta = Consulta(
                principio_ativo=principio_ativo,
                concentracao=concentracao,
                comprimidos=int(comprimidos),
                caixas=int(caixas),
                marcas_aceitas=marcas,
                cep=cep,
            )
            resultado = pesquisar(principio_ativo, consulta=consulta)
            st.session_state["ultima_busca"] = resultado
            if resultado["ofertas"]:
                registrar_pesquisa_automatica(
                    principio_ativo,
                    resultado["ofertas"],
                    int(caixas),
                )
        except (ValueError, PesquisaIndisponivelError) as erro:
            st.session_state["ultima_busca"] = None
            st.error(str(erro))

ultima_busca = st.session_state.get("ultima_busca")
if ultima_busca:
    st.subheader("Resultado da busca")
    status_fontes = []
    for fonte in ultima_busca["fontes"]:
        if fonte["status"] == "ok":
            detalhe = f"{fonte['quantidade']} oferta(s)"
        elif fonte["status"] == "sem_ofertas":
            detalhe = "sem oferta compatível"
        else:
            detalhe = "indisponível"
        status_fontes.append(f"{fonte['nome']}: {detalhe}")
    st.caption(" · ".join(status_fontes))

    ranking = ordenar_por_preco_produtos(ultima_busca["ofertas"])
    if not ranking:
        st.info(
            "Nenhuma oferta bateu com princípio ativo, 300 mg e a quantidade "
            "de comprimidos informada."
        )
    else:
        ofertas_com_frete = [
            oferta
            for oferta in ranking
            if oferta.get("frete_confirmado") and oferta.get("frete") is not None
        ]
        menor_preco_caixa = min(
            oferta["preco_produtos"] for oferta in ranking
        )
        melhor = ofertas_com_frete[0] if ofertas_com_frete else ranking[0]
        estimado = melhor["preco_produtos"] * int(caixas)
        metrica1, metrica2, metrica3 = st.columns(3)
        metrica1.metric(
            "Menor preço por caixa",
            formatar_moeda(menor_preco_caixa),
        )
        if ofertas_com_frete:
            melhor_total = (
                ofertas_com_frete[0]["preco_produtos"] * int(caixas)
                + ofertas_com_frete[0]["frete"]
            )
            metrica2.metric("Menor total com frete", formatar_moeda(melhor_total))
            metrica3.metric(
                "Farmácia com menor total",
                ofertas_com_frete[0]["farmacia"],
            )
        else:
            metrica2.metric(
                f"Estimativa para {int(caixas)} caixa(s)",
                formatar_moeda(estimado),
            )
            metrica3.metric(
                "Menor subtotal",
                formatar_moeda(estimado),
                help=f"Farmácia: {melhor['farmacia']}; frete não cotado.",
            )

        st.caption(
            f"{melhor['produto']} — o total com frete para o CEP {cep or 'informado'} "
            "é calculado para a quantidade de caixas e CEP informados quando "
            "a farmácia disponibiliza cotação automática."
        )

        linhas = []
        for oferta in ranking:
            frete = oferta.get("frete")
            frete_disponivel = (
                frete is not None and oferta.get("frete_confirmado")
            )

            linhas.append(
                {
                    "Farmácia": oferta["farmacia"],
                    "Produto": oferta["produto"],
                    "Tipo": oferta["produto_tipo"],
                    "Laboratório": oferta.get("laboratorio") or "",
                    "Origem": oferta.get("origem") or "",
                    "Caixa (R$)": oferta["preco_produtos"] / 100,
                    f"{int(caixas)} caixa(s) (R$)": oferta["preco_produtos"] * int(caixas) / 100,
                    "Frete (R$)": (
                        frete / 100 if frete_disponivel else None
                    ),
                    "Total com frete (R$)": (
                        oferta["preco_produtos"] * oferta.get("caixas", int(caixas))
                        + frete
                    )
                    / 100
                    if frete_disponivel
                    else None,
                    "Status do frete": (
                        "Calculado"
                        if frete_disponivel
                        else oferta.get("frete_erro") or "Não disponível"
                    ),
                    "Estoque no site": bool(oferta.get("estoque_confirmado")),
                    "Link": oferta.get("url") or "",
                }
            )

        tabela_busca = pd.DataFrame(linhas)
        st.dataframe(
            tabela_busca,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Link": st.column_config.LinkColumn("Abrir oferta"),
                "Caixa (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                f"{int(caixas)} caixa(s) (R$)": st.column_config.NumberColumn(
                    format="R$ %.2f"
                ),
                "Frete (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Total com frete (R$)": st.column_config.NumberColumn(
                    format="R$ %.2f"
                ),
            },
        )

st.info(
    "Panvel e Drogasil continuam no comparador, mas os sites delas impedem "
    "leitura automática. Para essas lojas, e para ofertas sem cotação de frete, "
    "use “Registrar observação manual” para completar os valores."
)

st.subheader("Registrar observação manual")
with st.form("registro_oferta_manual", clear_on_submit=True):
    farmacia_nomes = sorted({farmacia["nome"] for farmacia in FARMACIAS} | {"Outra"})
    farmacia = st.selectbox("Farmácia observada", farmacia_nomes)
    produto = st.text_input(
        "Nome exato do produto exibido na farmácia",
        placeholder=(
            "Ex.: Ácido Ursodesoxicólico 300mg com 30 comprimidos - "
            "Ranbaxy Genérico"
        ),
    ).strip()
    tipo_produto = st.selectbox(
        "Tipo de produto",
        ["Marca", "Genérico", "Similar", "Não identificado"],
    )
    url = st.text_input("Link do produto (opcional)")
    preco_produtos = st.number_input(
        "Preço dos produtos (R$)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
    )
    frete = st.number_input(
        "Frete (R$), se conhecido",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
    )
    produto_confirmado = st.checkbox(
        "Conferi princípio ativo, concentração e apresentação do produto"
    )
    frete_confirmado = st.checkbox("Frete confirmado para o CEP informado")
    estoque_confirmado = st.checkbox("Estoque confirmado")
    registrar = st.form_submit_button("Registrar observação")

    if registrar:
        if not principio_ativo:
            st.error("Informe o princípio ativo na barra lateral.")
        elif not produto:
            st.error("Informe o nome do produto observado.")
        elif preco_produtos <= 0:
            st.error("O preço dos produtos deve ser maior que zero.")
        elif frete_confirmado and frete is None:
            st.error("Informe o valor do frete antes de marcá-lo como confirmado.")
        else:
            preco_centavos = int(
                (Decimal(str(preco_produtos)) * 100).quantize(Decimal("1"))
            )
            frete_centavos = (
                int((Decimal(str(frete)) * 100).quantize(Decimal("1")))
                if frete is not None
                else None
            )
            registrar_oferta_manual(
                medicamento=principio_ativo,
                farmacia=farmacia,
                produto=produto,
                produto_tipo=tipo_produto,
                url=url.strip() or None,
                preco_produtos=preco_centavos,
                frete=frete_centavos,
                caixas=int(caixas),
                produto_confirmado=produto_confirmado,
                frete_confirmado=frete_confirmado,
                estoque_confirmado=estoque_confirmado,
            )
            st.success("Observação manual registrada no histórico.")
            st.rerun()

st.subheader("Histórico de observações")
historico = obter_historico(medicamento=principio_ativo or None)
if not historico:
    st.info("Ainda não há observações para este princípio ativo.")
else:
    ofertas_validas = comparar_ofertas(historico)
    if ofertas_validas:
        melhor = ofertas_validas[0]
        st.metric(
            "Menor total confirmado",
            formatar_moeda(melhor["preco_total"]),
            help="Considera apenas produto, frete e estoque confirmados.",
        )
    else:
        st.caption(
            "Ainda não há ofertas com produto, frete e estoque confirmados "
            "para comparação de total."
        )

    tabela = pd.DataFrame(historico)
    tabela["preco_produtos"] = tabela["preco_produtos"] / 100
    tabela["frete"] = tabela["frete"].apply(
        lambda valor: valor / 100 if pd.notna(valor) else None
    )
    tabela["preco_total"] = tabela["preco_total"].apply(
        lambda valor: valor / 100 if pd.notna(valor) else None
    )
    tabela = tabela.rename(
        columns={
            "data_consulta": "Consulta",
            "farmacia": "Farmácia",
            "produto": "Produto",
            "produto_tipo": "Tipo",
            "preco_produtos": "Produtos (R$)",
            "frete": "Frete (R$)",
            "preco_total": "Total confirmado (R$)",
            "produto_confirmado": "Produto conferido",
            "frete_confirmado": "Frete confirmado",
            "estoque_confirmado": "Estoque confirmado",
            "origem": "Origem",
        }
    )
    colunas = [
        "Consulta",
        "Farmácia",
        "Produto",
        "Tipo",
        "Produtos (R$)",
        "Frete (R$)",
        "Total confirmado (R$)",
        "Produto conferido",
        "Frete confirmado",
        "Estoque confirmado",
        "Origem",
    ]
    st.dataframe(tabela[colunas], use_container_width=True, hide_index=True)

    historico_grafico = tabela.dropna(subset=["Total confirmado (R$)"])
    if not historico_grafico.empty:
        historico_grafico = historico_grafico.sort_values("Consulta")
        st.subheader("Evolução dos totais confirmados")
        st.line_chart(
            historico_grafico.set_index("Consulta")["Total confirmado (R$)"]
        )

with st.expander("Configuração aplicada"):
    st.write(
        {
            "princípio ativo": principio_ativo,
            "concentração": concentracao,
            "comprimidos por caixa": int(comprimidos),
            "caixas desejadas": int(caixas),
            "marcas aceitas": marcas,
            "CEP": cep,
            "intervalo de monitoramento (dias)": int(intervalo_dias),
            "desconto para alerta (%)": desconto_alerta,
        }
    )

st.caption(
    "Medicamento de venda sob prescrição. Confira bula, estoque, validade "
    "e o valor final no site da farmácia antes de comprar."
)
