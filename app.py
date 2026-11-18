"""Três telas; somente exportações agregadas; uma competência por execução."""
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from tccbi.core import summary, strict_sum
from tccbi.pipeline import load_prepared, read_json, digest

st.set_page_config(page_title="BI SIH/CNES — DF", layout="wide")
st.title("Produção hospitalar do SUS e leitos cadastrados — DF")
st.caption("Protótipo de pesquisa • análise retrospectiva • sem validação com gestores")
path = os.environ.get("TCC_RUN", "")
if not path:
    st.info("Defina TCC_RUN com a pasta de uma execução concluída. Consulte o README.")
    st.stop()
run = Path(path)
try:
    evaluation = read_json(run / "avaliacao.json")
    manifest = read_json(run / "manifesto.json")
    if evaluation["manifesto_sha256"] != digest(run / "manifesto.json"):
        raise ValueError("Manifesto alterado após build")
    if evaluation["inputs_preparados"] != read_json(run / "preparacao.json"):
        raise ValueError("Preparação mudou: execute build novamente")
    rd, cadastro, lt = load_prepared(run)
    for file, sha in evaluation["outputs"].items():
        if digest(run / file) != sha:
            raise ValueError("Saída analítica alterada após avaliação")
    view = pd.read_parquet(run / "analytics/estabelecimentos.parquet")
except Exception as exc:
    st.error(f"Execução incompleta ou inconsistente: {exc}")
    st.stop()

if manifest.get("dados") == "sinteticos":
    st.error("DADOS SINTÉTICOS DE TESTE — NÃO SÃO RESULTADOS DO DF")
st.warning("Resultados não conciliados com o TABNET. Não representam ocupação, custo econômico ou eficiência.")
st.caption(f"Competência de processamento/cadastro: {manifest['competencia']} • execução: {run.name}")
page = st.sidebar.radio("Tela", ["Visão geral", "Estabelecimentos", "Qualidade e rastreabilidade"])
selected = st.sidebar.multiselect("CNES com produção (vazio = todos)", sorted(rd.CNES.unique()))
r = rd.loc[rd.CNES.isin(selected)].copy() if selected else rd
v = view.loc[view.CNES.isin(selected)].copy() if selected else view

def display_number(value, decimals=0):
    return "Não calculável" if value is None or pd.isna(value) else f"{value:,.{decimals}f}"

if page == "Visão geral":
    s = summary(r)
    cols = st.columns(3)
    cols[0].metric("Registros de AIH aprovadas", s["aih_registros"])
    cols[1].metric("AIHs normais — IDENT=1", s["aih_normais"])
    cols[2].metric("AIHs de prorrogação — IDENT=5", s["aih_prorrogacao"])
    total = s["valor_total_centavos"]
    st.metric("Valor aprovado — R$", display_number(None if total is None else total / 100, 2))
    st.metric("Valor médio por registro de AIH — R$", display_number(s["valor_medio_reais"], 2))
    st.subheader("Permanência das AIHs normais")
    stats = {k: s[k] for k in ["permanencia_media", "permanencia_mediana", "permanencia_q1", "permanencia_q3"]}
    st.dataframe(pd.DataFrame([stats]), hide_index=True)
    st.caption(f"Dias registrados em IDENT=1. Ausências: {s['n_permanencia_ausente']}. Quartis com interpolação linear. Não reconstrói episódios completos.")
    st.subheader("Estrutura dos estabelecimentos selecionados com produção")
    st.metric("Leitos existentes — todas as categorias LT", display_number(strict_sum(v.leitos_existentes)))
    st.metric("Leitos SUS cadastrados — todas as categorias LT", display_number(strict_sum(v.leitos_sus)))
    st.caption("Não inclui estabelecimentos sem produção no RD. Categorias complementares não foram equiparadas a leitos gerais. Razões disponíveis por estabelecimento na segunda tela.")
    specialty = r.groupby("ESPEC", dropna=False).size().rename("registros_aih").reset_index()
    specialty["ESPEC"] = specialty.ESPEC.fillna("Não informado")
    st.plotly_chart(px.bar(specialty, x="ESPEC", y="registros_aih", labels={"ESPEC":"Código da especialidade RD", "registros_aih":"Registros de AIH"}), width="stretch")
    st.caption("Códigos originais; rótulos de domínio ainda devem ser conferidos na tabela oficial. Não há associação automática com CODLEITO.")
elif page == "Estabelecimentos":
    st.caption("Uma linha por CNES e competência. AIH/leito é uma razão descritiva, não taxa de ocupação ou giro.")
    st.dataframe(v, hide_index=True)
    st.download_button("Exportar agregados do recorte", v.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"estabelecimentos_{manifest['competencia']}.csv", mime="text/csv")
    st.subheader("Composição dos leitos no recorte")
    chosen_lt = lt.loc[lt.CNES.isin(v.CNES)]
    composition = chosen_lt.groupby(["TP_LEITO", "CODLEITO"], dropna=False)[["leitos_existentes", "leitos_sus"]].agg(strict_sum).reset_index()
    st.dataframe(composition, hide_index=True)
else:
    st.subheader("Escopo e pendências")
    st.write("Dados públicos secundários; resultados agregados. Piloto técnico não substitui conciliação com o TABNET nem avaliação por usuários.")
    st.json(evaluation)
    st.subheader("Manifesto de entrada")
    st.json(manifest)
    st.subheader("Perfil dos arquivos")
    st.json(read_json(run / "perfil.json"))
