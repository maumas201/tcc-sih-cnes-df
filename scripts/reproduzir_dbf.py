"""Reexecuta a integração sobre os DBF identificados pelo inventário do piloto."""
import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.conferir_dbf import registros
from tccbi.core import REQUIRED, pilot, prepare
from tccbi.pipeline import digest


def reproduzir(execucao):
    raiz = Path(__file__).resolve().parents[1]
    inventario = json.loads((raiz / "config/inventario_piloto_anterior.json").read_text(encoding="utf-8"))
    preparados = {}
    for item in inventario:
        nome = item["arquivo"]
        tipo = nome[:2]
        dbf = execucao / "converted" / f"{tipo}.dbf"
        if digest(dbf) != item["sha256_dbf"] or digest(execucao / "raw" / nome) != item["sha256"]:
            raise ValueError(f"Conteúdo diferente do inventário original: {tipo}")
        dados = pd.DataFrame(registros(dbf, REQUIRED[tipo]))
        preparados[tipo] = prepare(dados, tipo, "202506")
    resultado = pilot(preparados["RD"], preparados["ST"], preparados["LT"])
    esperado = json.loads((raiz / "evidencias/piloto.json").read_text(encoding="utf-8"))
    if resultado != esperado:
        raise ValueError("Resultado diverge do piloto")
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("execucao", type=Path)
    print(json.dumps(reproduzir(parser.parse_args().execucao), ensure_ascii=False, indent=2))
