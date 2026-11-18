"""Gera evidências agregadas, sem copiar microdados para a pasta de entrega."""
import argparse
from pathlib import Path
from .pipeline import read_json, write_json, load_prepared, digest
from .core import summary, beds

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("evidencias/piloto_real"))
    a=p.parse_args()
    rd,st,lt=load_prepared(a.run)
    a.output.mkdir(parents=True,exist_ok=True)
    previous=read_json(Path(__file__).resolve().parents[1]/"config/inventario_piloto_anterior.json")
    manifest=read_json(a.run/"manifesto.json")
    hashes={k:any(x["sha256"]==v["sha256"] for x in previous) for k,v in manifest["arquivos"].items()}
    results={"hashes_coincidem_inventario_anterior":hashes,
             "indicadores":summary(rd),"estabelecimentos_rd":int(rd.CNES.nunique()),
             "estabelecimentos_st":int(st.CNES.nunique()),"estabelecimentos_lt":int(lt.CNES.nunique()),
             "leitos_todos_lt": {"existentes":int(lt.leitos_existentes.sum()),"sus":int(lt.leitos_sus.sum())},
             "leitos_cnes_com_rd":{"existentes":int(lt.loc[lt.CNES.isin(rd.CNES),"leitos_existentes"].sum()),
                                    "sus":int(lt.loc[lt.CNES.isin(rd.CNES),"leitos_sus"].sum())}}
    write_json(a.output/"resumo_reproduzido.json",results)
    for name in ["manifesto.json","perfil.json","preparacao.json","piloto.json","avaliacao.json"]:
        write_json(a.output/name,read_json(a.run/name))
    # Comparação simples reproduzível dos tamanhos relatados versus observados.
    profile=read_json(a.run/"perfil.json")
    rows=["# Reprodução do piloto — dados originais anexados", "",
          "Não houve autenticação do download original nem conciliação com o TABNET.","",
          "| Base | Registros | Campos |", "|---|---:|---:|"]
    for k,v in profile.items(): rows.append(f"| {k} | {v['registros']} | {v['campos']} |")
    experiment=read_json(a.run/"piloto.json")
    rows.extend(["", "## Experimento de integração", "", "```json",
                 __import__('json').dumps(experiment,ensure_ascii=False,indent=2),"```",
                 "", "Resultados calculados pelo código entregue. Veja resumo_reproduzido.json para estatísticas adicionais."])
    (a.output/"RELATORIO.md").write_text("\n".join(rows),encoding="utf-8")

if __name__ == "__main__": main()
