"""CLI: ingest -> profile -> prepare -> pilot -> build. Não sobrescreve execuções."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time
import urllib.request
import uuid
import pandas as pd
from .core import REQUIRED, prepare, integrate, pilot

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    tmp.replace(path)

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def environment():
    packages = {}
    for name in ["pandas", "pyarrow", "pyreaddbc", "dbfread", "streamlit", "plotly", "pytest"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "não instalado"
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "sem commit disponível"
    root = Path(__file__).resolve().parents[1]
    sources = {str(p.relative_to(root)): digest(p) for p in sorted(root.glob("tccbi/*.py"))}
    sources["app.py"] = digest(root / "app.py")
    return {"python": platform.python_version(), "plataforma": platform.platform(),
            "pacotes": packages, "commit": commit, "codigo_sha256": sources}

def urls(competence):
    if not re.fullmatch(r"20[0-9]{2}(0[1-9]|1[0-2])", competence):
        raise ValueError("Competência deve ser AAAAMM")
    suffix = competence[2:]
    base = "ftp://ftp.datasus.gov.br/dissemin/publicos/"
    return {
        "RD": base + f"SIHSUS/200801_/Dados/RDDF{suffix}.dbc",
        "ST": base + f"CNES/200508_/Dados/ST/STDF{suffix}.dbc",
        "LT": base + f"CNES/200508_/Dados/LT/LTDF{suffix}.dbc",
    }

def ingest(run, competence, source=None):
    mapping = urls(competence)
    run.mkdir(parents=True, exist_ok=False)
    raw = run / "raw"
    raw.mkdir()
    manifest = {"competencia": competence, "uf": "DF", "dados": "reais_não_conciliados",
                "criado_utc": datetime.now(timezone.utc).isoformat(), "arquivos": {},
                "ambiente_ingestao": environment()}
    for kind, url in mapping.items():
        name = url.rsplit("/", 1)[1]
        target = raw / name
        temp = target.with_suffix(".part")
        if source:
            local = Path(source) / name
            if not local.is_file():
                raise FileNotFoundError(local)
            shutil.copyfile(local, temp)
            origin = "cópia local; origem anterior não autenticada pelo programa"
        else:
            with urllib.request.urlopen(url, timeout=45) as response, temp.open("wb") as out:
                shutil.copyfileobj(response, out)
            origin = "download direto"
        if temp.stat().st_size < 32 or temp.read_bytes()[:100].lstrip().lower().startswith((b"<html", b"<!doctype")):
            raise ValueError(f"Arquivo inválido recebido: {kind}")
        temp.replace(target)
        manifest["arquivos"][kind] = {"arquivo": str(target.relative_to(run)),
            "url_oficial_prevista": url, "origem": origin, "bytes": target.stat().st_size,
            "sha256": digest(target), "obtido_utc": datetime.now(timezone.utc).isoformat()}
        previous = Path(__file__).resolve().parents[1] / "config/inventario_piloto_anterior.json"
        if competence == "202506" and previous.exists():
            old = {x["arquivo"]: x for x in read_json(previous)}
            manifest["arquivos"][kind]["hash_coincide_inventario_anterior"] = digest(target) == old[name]["sha256"]
        write_json(run / "manifesto.json", manifest)
    return manifest

def verify_inputs(run):
    manifest = read_json(run / "manifesto.json")
    if set(manifest["arquivos"]) != {"RD", "ST", "LT"}:
        raise ValueError("Aquisição incompleta")
    for item in manifest["arquivos"].values():
        if digest(run / item["arquivo"]) != item["sha256"]:
            raise ValueError("Arquivo de entrada alterado desde o manifesto")
    return manifest

def profile(run):
    from dbfread import DBF, FieldParser
    from pyreaddbc import dbc2dbf
    class ExactParser(FieldParser):
        def parseN(self, field, data):
            value = data.strip().strip(b"\x00")
            return Decimal(value.decode("ascii")) if value else None

    manifest = verify_inputs(run)
    out = run / "converted"
    out.mkdir(exist_ok=True)
    results = {}
    for kind, item in manifest["arquivos"].items():
        dbf = out / f"{kind}.dbf"
        dbc2dbf(str(run / item["arquivo"]), str(dbf))
        table = DBF(str(dbf), encoding="latin-1", parserclass=ExactParser, load=True)
        # Strings conservam representações decimais e códigos no estágio intermediário.
        df = pd.DataFrame([{k: None if v is None else str(v) for k, v in row.items()} for row in table],
                          columns=table.field_names).astype("string")
        df = df.replace(r"^\s*$", pd.NA, regex=True)
        df.to_parquet(out / f"{kind}.parquet", index=False)
        results[kind] = {"registros": len(df), "campos": len(df.columns),
                         "registros_marcados_excluidos": len(table.deleted),
                         "duplicatas_integrais": int(df.duplicated().sum()),
                         "campos_requeridos_ausentes": sorted(set(REQUIRED[kind]) - set(df.columns)),
                         "parquet_sha256": digest(out / f"{kind}.parquet"),
                         "layout": [{"campo": f.name, "tipo_dbf": f.type, "tamanho": f.length,
                                     "decimais": f.decimal_count, "ausentes": int(df[f.name].isna().sum()),
                                     "distintos": int(df[f.name].nunique())} for f in table.fields]}
    if manifest["competencia"] == "202506":
        reported = {"RD": [21120, 114], "ST": [6189, 208], "LT": [568, 28]}
        for kind, pair in reported.items():
            results[kind]["relato_anterior_nao_verificado"] = pair
            results[kind]["coincide_com_relato"] = [results[kind]["registros"], results[kind]["campos"]] == pair
    write_json(run / "perfil.json", results)
    return results

def prepare_all(run):
    manifest = verify_inputs(run)
    profiles = read_json(run / "perfil.json")
    out = run / "prepared"
    out.mkdir(exist_ok=True)
    report = {}
    for kind in ["RD", "ST", "LT"]:
        path = run / "converted" / f"{kind}.parquet"
        if digest(path) != profiles[kind]["parquet_sha256"]:
            raise ValueError("Estágio convertido alterado; refaça perfilamento")
        if profiles[kind]["registros_marcados_excluidos"]:
            raise ValueError("DBF contém registros excluídos: investigar política antes de prosseguir")
        raw = pd.read_parquet(path)
        df = prepare(raw, kind, manifest["competencia"])
        df.to_parquet(out / f"{kind}.parquet", index=False)
        report[kind] = {"entrada": len(raw), "saida": len(df), "excluidos": 0,
                        "parquet_sha256": digest(out / f"{kind}.parquet")}
    write_json(run / "preparacao.json", report)
    return report

def load_prepared(run):
    verify_inputs(run)
    report = read_json(run / "preparacao.json")
    frames = []
    for kind in ["RD", "ST", "LT"]:
        path = run / "prepared" / f"{kind}.parquet"
        if digest(path) != report[kind]["parquet_sha256"]:
            raise ValueError("Estágio preparado alterado; refaça preparação")
        frames.append(pd.read_parquet(path))
    return frames

def build(run):
    start = time.perf_counter()
    rd, st, lt = load_prepared(run)
    result = pilot(rd, st, lt)
    out = run / "analytics"
    out.mkdir(exist_ok=True)
    view = integrate(rd, st, lt)
    view.to_parquet(out / "estabelecimentos.parquet", index=False)
    # Não publica dados individuais na UI/exportações; detalhe local para métricas.
    result["segundos_build"] = time.perf_counter() - start
    result["ambiente_build"] = environment()
    result["outputs"] = {"analytics/estabelecimentos.parquet": digest(out / "estabelecimentos.parquet")}
    result["inputs_preparados"] = read_json(run / "preparacao.json")
    result["manifesto_sha256"] = digest(run / "manifesto.json")
    result["tabnet"] = "não conciliado"
    result["validacao_usuarios"] = "não realizada; fora do escopo"
    write_json(run / "avaliacao.json", result)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["ingest", "profile", "prepare", "pilot", "build"])
    parser.add_argument("--run", type=Path)
    parser.add_argument("--competence", default="202506")
    parser.add_argument("--source-dir", type=Path)
    args = parser.parse_args()
    if args.step != "ingest" and not args.run:
        parser.error("--run é obrigatório após ingest")
    run = args.run or Path("runs") / (args.competence + "_" + uuid.uuid4().hex[:8])
    start = time.perf_counter()
    try:
        if args.step == "ingest":
            result = ingest(run, args.competence, args.source_dir)
        elif args.step == "profile":
            result = profile(run)
        elif args.step == "prepare":
            result = prepare_all(run)
        elif args.step == "pilot":
            result = pilot(*load_prepared(run))
            write_json(run / "piloto.json", result)
        else:
            result = build(run)
        write_json(run / f"etapa_{args.step}.json", {"etapa": args.step, "sucesso": True,
            "segundos": time.perf_counter() - start, "ambiente": environment()})
        print(json.dumps({"run": str(run), "etapa": args.step, "sucesso": True}, ensure_ascii=False))
    except Exception as exc:
        # A falha é explícita: não converte erro de dados em resultado vazio.
        if run.exists():
            write_json(run / f"falha_{args.step}_{uuid.uuid4().hex[:8]}.json",
                       {"etapa": args.step, "erro": str(exc), "tipo": type(exc).__name__})
        raise

if __name__ == "__main__":
    main()
