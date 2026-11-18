"""Transformações e indicadores puros; nenhuma leitura de arquivo ou UI."""
from decimal import Decimal, InvalidOperation
import pandas as pd

KEY = ["CNES", "competencia"]
REQUIRED = {
    "RD": ["CNES", "ANO_CMPT", "MES_CMPT", "MUNIC_MOV", "N_AIH",
           "IDENT", "ESPEC", "DIAS_PERM", "VAL_TOT"],
    "ST": ["CNES", "COMPETEN", "CODUFMUN"],
    "LT": ["CNES", "COMPETEN", "CODUFMUN", "TP_LEITO", "CODLEITO", "QT_EXIST", "QT_SUS"],
}

def code(series, width, allow_missing=False):
    """Conserva zeros; rejeita decimais, sinais e caracteres não numéricos."""
    s = series.astype("string").str.strip().replace("", pd.NA)
    bad = s.notna() & ~s.str.fullmatch(r"[0-9]{1," + str(width) + "}", na=False)
    if bad.any() or (not allow_missing and s.isna().any()):
        raise ValueError(f"Código inválido/ausente em {series.name}: {int(bad.sum())} inválidos")
    return s.str.zfill(width)

def integer(series):
    values = []
    for value in series:
        if pd.isna(value) or str(value).strip() == "":
            values.append(pd.NA)
            continue
        try:
            d = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"Número inválido em {series.name}") from exc
        if not d.is_finite() or d < 0 or d != d.to_integral_value():
            raise ValueError(f"Inteiro não negativo exigido em {series.name}")
        values.append(int(d))
    return pd.Series(values, index=series.index, dtype="Int64", name=series.name)

def cents(series):
    """VAL_TOT em reais -> centavos inteiros; não arredonda erros silenciosamente."""
    values = []
    for value in series:
        if pd.isna(value) or str(value).strip() == "":
            values.append(pd.NA)
            continue
        try:
            d = Decimal(str(value)) * 100
        except InvalidOperation as exc:
            raise ValueError("VAL_TOT inválido") from exc
        if not d.is_finite() or d < 0 or d != d.to_integral_value():
            raise ValueError("VAL_TOT negativo/não finito/com fração menor que centavo")
        values.append(int(d))
    return pd.Series(values, index=series.index, dtype="Int64")

def strict_sum(series):
    """Ausência em qualquer parcela torna o total desconhecido, não zero."""
    if series.empty or series.isna().any():
        return None
    return int(series.sum())

def prepare(frame, kind, competence):
    missing = set(REQUIRED[kind]) - set(frame.columns)
    if missing:
        raise ValueError(f"{kind}: campos ausentes: {sorted(missing)}")
    if frame.empty:
        raise ValueError(f"{kind}: arquivo vazio")
    if frame.duplicated().any():
        raise ValueError(f"{kind}: linhas integralmente repetidas; investigar, não excluir automaticamente")
    d = frame[REQUIRED[kind]].copy()
    d["CNES"] = code(d.CNES, 7)
    if d.CNES.eq("0000000").any():
        raise ValueError("CNES zero: investigar chave")
    if kind == "RD":
        d["competencia"] = code(d.ANO_CMPT, 4) + code(d.MES_CMPT, 2)
        d["MUNIC_MOV"] = code(d.MUNIC_MOV, 6)
        municipality = d.MUNIC_MOV
        d["N_AIH"] = code(d.N_AIH, 13)
        d["IDENT"] = code(d.IDENT, 1)
        if not d.IDENT.isin(["1", "5"]).all():
            raise ValueError("IDENT fora de 1/5: rever domínio oficial")
        d["ESPEC"] = code(d.ESPEC, 2, allow_missing=True)
        d["dias"] = integer(d.DIAS_PERM)
        d["valor_centavos"] = cents(d.VAL_TOT)
    else:
        d["competencia"] = code(d.COMPETEN, 6)
        # O layout histórico descreve char(7), mas município UF+MUNIC sem DV.
        # Aceita seis dígitos; divergência exige inspeção, não truncamento.
        d["CODUFMUN"] = code(d.CODUFMUN, 6)
        municipality = d.CODUFMUN
        if kind == "LT":
            d["TP_LEITO"] = code(d.TP_LEITO, 2)
            d["CODLEITO"] = code(d.CODLEITO, 2)
            d["leitos_existentes"] = integer(d.QT_EXIST)
            d["leitos_sus"] = integer(d.QT_SUS)
            if (d.leitos_sus > d.leitos_existentes).fillna(False).any():
                raise ValueError("LT: SUS maior que existentes; investigar registro")
            if d.duplicated(KEY + ["TP_LEITO", "CODLEITO"]).any():
                raise ValueError("LT: grão candidato repetido; investigar outras dimensões")
        elif d.duplicated(KEY).any():
            raise ValueError("ST: CNES/competência não único")
    if not d.competencia.eq(competence).all():
        raise ValueError(f"{kind}: competência interna diverge do arquivo/recorte")
    if not municipality.str.startswith("53").all():
        raise ValueError(f"{kind}: município fora do DF; investigar recorte")
    d["linha_origem"] = range(1, len(d) + 1)
    return d

def summary(rd):
    """Estatísticas por registro aprovado; permanência restringe IDENT=1."""
    n = len(rd)
    normal = rd.loc[rd.IDENT.eq("1"), "dias"]
    valid = normal.dropna()
    total = strict_sum(rd.valor_centavos)
    complete = len(valid) == len(normal) and len(normal) > 0
    return {
        "aih_registros": n,
        "aih_normais": int(rd.IDENT.eq("1").sum()),
        "aih_prorrogacao": int(rd.IDENT.eq("5").sum()),
        "numeros_aih_distintos": int(rd.N_AIH.nunique()),
        "valor_total_centavos": total,
        "valor_medio_reais": total / 100 / n if total is not None and n else None,
        "dias_normais_total": strict_sum(normal),
        "n_permanencia_valida": len(valid),
        "n_permanencia_ausente": int(normal.isna().sum()),
        "permanencia_media": float(valid.mean()) if complete else None,
        "permanencia_mediana": float(valid.median()) if complete else None,
        "permanencia_q1": float(valid.quantile(.25, interpolation="linear")) if complete else None,
        "permanencia_q3": float(valid.quantile(.75, interpolation="linear")) if complete else None,
    }

def production(rd):
    rows = []
    for keys, group in rd.groupby(KEY, dropna=False, sort=True):
        rows.append(dict(zip(KEY, keys)) | summary(group))
    return pd.DataFrame(rows, dtype=object)

def beds(lt):
    rows = []
    for keys, group in lt.groupby(KEY, dropna=False, sort=True):
        rows.append(dict(zip(KEY, keys)) | {
            "leitos_existentes": strict_sum(group.leitos_existentes),
            "leitos_sus": strict_sum(group.leitos_sus),
        })
    return pd.DataFrame(rows, dtype=object)

def integrate(rd, st, lt):
    p, b = production(rd), beds(lt)
    view = p.merge(b, on=KEY, how="left", validate="one_to_one", indicator="juncao_lt")
    view = view.merge(st[KEY], on=KEY, how="left", validate="one_to_one", indicator="juncao_st")
    view["aih_por_leito_sus"] = view.aih_registros.div(view.leitos_sus.where(view.leitos_sus.gt(0)))
    if int(view.aih_registros.sum()) != len(rd):
        raise AssertionError("Conservação das AIHs falhou")
    before = strict_sum(rd.valor_centavos)
    after = strict_sum(view.valor_total_centavos)
    if before != after:
        raise AssertionError("Conservação do valor falhou")
    return view

def pilot(rd, st, lt):
    # Experimento propositalmente incorreto, restrito a colunas mínimas.
    # Limite de memória: estimar cardinalidade antes de materializar.
    m = rd.groupby(KEY).size().to_frame("n_rd").join(lt.groupby(KEY).size().rename("n_lt"))
    expected = int((m.n_rd * m.n_lt.fillna(1)).sum())
    if expected > 2_000_000:
        raise ValueError("Junção ingênua excede limite experimental; não materializada")
    naive = rd[KEY + ["valor_centavos"]].merge(lt[KEY], on=KEY, how="left")
    good = integrate(rd, st, lt)
    return {
        "rd_linhas": len(rd), "junção_direta_linhas": len(naive),
        "fator_multiplicacao": len(naive) / len(rd),
        "valor_original_centavos": strict_sum(rd.valor_centavos),
        "valor_juncao_direta_centavos": strict_sum(naive.valor_centavos),
        "valor_integracao_centavos": strict_sum(good.valor_total_centavos),
        "aih_antes": len(rd), "aih_depois": int(good.aih_registros.sum()),
        "rd_sem_lt": int(good.loc[good.juncao_lt.eq("left_only"), "aih_registros"].sum()),
        "rd_sem_st": int(good.loc[good.juncao_st.eq("left_only"), "aih_registros"].sum()),
        "st_sem_rd": len(st[KEY].merge(good[KEY], on=KEY, how="left", indicator=True).query('_merge == "left_only"')),
        "lt_sem_rd": len(beds(lt)[KEY].merge(good[KEY], on=KEY, how="left", indicator=True).query('_merge == "left_only"')),
        "status": "execução técnica; não equivale à conciliação TABNET",
    }
