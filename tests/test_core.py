"""Casos sintéticos com valores deliberadamente escolhidos, não dados do DF."""
import pandas as pd
import pytest
from tccbi.core import prepare, integrate, pilot, summary, cents, code, strict_sum

@pytest.fixture
def raw():
    rd = pd.DataFrame({"CNES":["123", "123", "456"], "ANO_CMPT":["2025"]*3,
        "MES_CMPT":["06"]*3, "MUNIC_MOV":["530010"]*3, "N_AIH":["1","2","3"],
        "IDENT":["1","1","5"], "ESPEC":["1","2","1"],
        "DIAS_PERM":["2","6","30"], "VAL_TOT":["100.01","200.02","300.03"]})
    st = pd.DataFrame({"CNES":["123","456","789"], "COMPETEN":["202506"]*3, "CODUFMUN":["530010"]*3})
    lt = pd.DataFrame({"CNES":["123","123","789"], "COMPETEN":["202506"]*3,
        "CODUFMUN":["530010"]*3, "TP_LEITO":["1"]*3, "CODLEITO":["1","2","1"],
        "QT_EXIST":["4","6","2"], "QT_SUS":["3","5","0"]})
    return rd, st, lt

@pytest.fixture
def frames(raw):
    return [prepare(f, k, "202506") for f,k in zip(raw,["RD","ST","LT"])]

def test_safe_join_and_naive_experiment(frames):
    result = pilot(*frames)
    assert result["junção_direta_linhas"] == 5
    assert result["valor_juncao_direta_centavos"] == 90009
    assert result["valor_original_centavos"] == result["valor_integracao_centavos"] == 60006
    assert result["aih_antes"] == result["aih_depois"] == 3
    assert result["rd_sem_lt"] == 1
    assert result["st_sem_rd"] == 1
    assert result["lt_sem_rd"] == 1

def test_distribution_and_money(frames):
    s = summary(frames[0])
    assert s["permanencia_media"] == 4
    assert s["permanencia_mediana"] == 4
    assert s["permanencia_q1"] == 3
    assert s["permanencia_q3"] == 5
    assert s["valor_medio_reais"] == pytest.approx(200.02)

def test_missing_join_is_not_zero(frames):
    view = integrate(*frames).set_index("CNES")
    assert pd.isna(view.loc["0000456", "leitos_sus"])
    assert pd.isna(view.loc["0000456", "aih_por_leito_sus"])
    assert view.loc["0000123", "aih_por_leito_sus"] == .25

def test_zero_denominator(frames):
    rd, st, lt = frames
    lt["leitos_sus"] = 0
    assert integrate(rd, st, lt).aih_por_leito_sus.isna().all()

@pytest.mark.parametrize("value", ["-1", "1.001", "NaN", "abc", "Infinity"])
def test_invalid_money(value):
    with pytest.raises(ValueError): cents(pd.Series([value]))

def test_decimal_exact():
    assert cents(pd.Series(["0.10","0.20"])).sum() == 30

def test_missing_measure_not_zero(frames):
    rd = frames[0].copy()
    rd.loc[0,"valor_centavos"] = pd.NA
    rd.loc[0,"dias"] = pd.NA
    s = summary(rd)
    assert s["valor_total_centavos"] is None
    assert s["permanencia_media"] is None
    assert strict_sum(pd.Series([1,None])) is None

def test_bad_key():
    with pytest.raises(ValueError): code(pd.Series([None]),7)
    with pytest.raises(ValueError): code(pd.Series(["123.0"]),7)

def test_wrong_competence(raw):
    with pytest.raises(ValueError): prepare(raw[0],"RD","202505")

def test_other_uf(raw):
    raw[0].loc[0,"MUNIC_MOV"] = "350010"
    with pytest.raises(ValueError): prepare(raw[0],"RD","202506")

def test_duplicate_st(raw):
    duplicated = pd.concat([raw[1],raw[1].iloc[[0]]],ignore_index=True)
    with pytest.raises(ValueError): prepare(duplicated,"ST","202506")

def test_duplicate_lt_grain(raw):
    row = raw[2].iloc[[0]].copy()
    row["QT_EXIST"] = "5"
    duplicated = pd.concat([raw[2],row],ignore_index=True)
    with pytest.raises(ValueError): prepare(duplicated,"LT","202506")

def test_does_not_mutate(frames):
    originals = [f.copy(deep=True) for f in frames]
    integrate(*frames)
    for original, now in zip(originals, frames): pd.testing.assert_frame_equal(original, now)

def test_large_money_no_float_loss(frames):
    rd,st,lt = frames
    rd.loc[0,"valor_centavos"] = 9007199254740993
    view = integrate(rd,st,lt)
    assert strict_sum(view.valor_total_centavos) == 9007199254790998
