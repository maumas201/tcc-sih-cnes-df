"""Auditoria independente de cardinalidade e valor sobre os DBF convertidos."""
import argparse
import json
import struct
from collections import Counter
from decimal import Decimal
from pathlib import Path


def registros(caminho, campos):
    """Lê somente campos ASCII numéricos necessários ao experimento."""
    with caminho.open("rb") as arquivo:
        cabecalho = arquivo.read(32)
        quantidade, inicio, largura = struct.unpack_from("<IHH", cabecalho, 4)
        posicao = 1  # o primeiro byte indica exclusão lógica
        fatias = {}
        while arquivo.tell() < inicio:
            descritor = arquivo.read(32)
            if descritor[:1] == b"\r":
                break
            nome = descritor[:11].split(b"\0")[0].decode("ascii")
            tamanho = descritor[16]
            if nome in campos:
                fatias[nome] = slice(posicao, posicao + tamanho)
            posicao += tamanho
        if set(fatias) != set(campos):
            raise ValueError(f"Campos ausentes em {caminho.name}")
        arquivo.seek(inicio)
        for _ in range(quantidade):
            linha = arquivo.read(largura)
            if len(linha) != largura:
                raise ValueError("DBF incompleto")
            if linha[:1] == b" ":
                yield {nome: linha[fatia].decode("ascii").strip() for nome, fatia in fatias.items()}


def conferir(pasta):
    tipos = Counter()
    for linha in registros(pasta / "LT.dbf", ["CNES", "COMPETEN"]):
        tipos[linha["CNES"], linha["COMPETEN"]] += 1
    contagens = Counter()
    valores = Counter()
    for linha in registros(pasta / "RD.dbf", ["CNES", "ANO_CMPT", "MES_CMPT", "VAL_TOT"]):
        chave = linha["CNES"], linha["ANO_CMPT"] + linha["MES_CMPT"].zfill(2)
        contagens[chave] += 1
        valores[chave] += int(Decimal(linha["VAL_TOT"]) * 100)
    if {mes for _, mes in contagens} != {"202506"} or {mes for _, mes in tipos} != {"202506"}:
        raise ValueError("O experimento requer junho de 2025")
    return {
        "rd_linhas": sum(contagens.values()),
        "junção_direta_linhas": sum(n * max(1, tipos[k]) for k, n in contagens.items()),
        "valor_original_centavos": sum(valores.values()),
        "valor_juncao_direta_centavos": sum(v * max(1, tipos[k]) for k, v in valores.items()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pasta_convertidos", type=Path)
    args = parser.parse_args()
    calculado = conferir(args.pasta_convertidos)
    salvo = json.loads((Path(__file__).resolve().parents[1] / "evidencias/piloto.json").read_text(encoding="utf-8"))
    if any(salvo[k] != v for k, v in calculado.items()):
        raise SystemExit("Divergência com o piloto registrado")
    print(json.dumps(calculado, ensure_ascii=False, indent=2))
