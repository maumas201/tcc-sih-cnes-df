"""Smoke test automatizado, não teste de usabilidade."""
import argparse
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest
from .pipeline import write_json

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("evidencias/app_real.json"))
    a=p.parse_args()
    os.environ["TCC_RUN"]=str(a.run.resolve())
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py")).run(timeout=30)
    result={}
    for page in ["Visão geral","Estabelecimentos","Qualidade e rastreabilidade"]:
        app.sidebar.radio[0].set_value(page).run(timeout=30)
        result[page]={"excecoes":len(app.exception),"erros":len(app.error)}
        if app.exception or app.error:
            raise AssertionError(f"Falha na tela {page}")
    write_json(a.output,result)

if __name__ == "__main__": main()
