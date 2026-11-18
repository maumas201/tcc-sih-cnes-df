import json
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from tccbi.pipeline import ingest, verify_inputs, digest, write_json, build
from test_core import raw, frames

def test_ingest_hash_tampering(tmp_path):
    source = tmp_path / "origem"
    source.mkdir()
    for prefix in ["RD","ST","LT"]:
        (source / f"{prefix}DF2506.dbc").write_bytes(b"FICTICIO"*10)
    run = tmp_path / "run"
    ingest(run,"202506",source)
    assert len(verify_inputs(run)["arquivos"]) == 3
    (run / "raw/RDDF2506.dbc").write_bytes(b"alterado")
    with pytest.raises(ValueError): verify_inputs(run)

def test_ingest_does_not_overwrite(tmp_path):
    with pytest.raises(FileExistsError): ingest(tmp_path,"202506")

def test_build_and_three_screens(tmp_path, frames, monkeypatch):
    run = tmp_path / "sintetico"
    (run / "raw").mkdir(parents=True)
    (run / "prepared").mkdir()
    manifest = {"competencia":"202506", "dados":"sinteticos", "arquivos":{}}
    prepared = {}
    for k,f in zip(["RD","ST","LT"],frames):
        raw_file = run / "raw" / f"{k}.fixture"
        raw_file.write_text("ARQUIVO FICTICIO; não é DBC")
        manifest["arquivos"][k] = {"arquivo":str(raw_file.relative_to(run)),"sha256":digest(raw_file)}
        path = run / "prepared" / f"{k}.parquet"
        f.to_parquet(path,index=False)
        prepared[k] = {"parquet_sha256":digest(path)}
    write_json(run / "manifesto.json",manifest)
    write_json(run / "preparacao.json",prepared)
    write_json(run / "perfil.json",{"status":"somente fixture sintética"})
    result = build(run)
    assert result["aih_depois"] == 3
    monkeypatch.setenv("TCC_RUN",str(run))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
    assert not app.exception
    assert any("SINTÉTICOS" in x.value for x in app.error)
    for page in ["Estabelecimentos", "Qualidade e rastreabilidade", "Visão geral"]:
        app.sidebar.radio[0].set_value(page).run(timeout=30)
        assert not app.exception
    app.sidebar.multiselect[0].set_value(["0000456"]).run(timeout=30)
    assert not app.exception
    # Ausência de LT não pode aparecer como zero.
    assert any(m.value == "Não calculável" for m in app.metric)
