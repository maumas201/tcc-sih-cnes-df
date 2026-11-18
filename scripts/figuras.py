"""Gera o gráfico do piloto e o esquema de interface usados no README."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter

raiz = Path(__file__).resolve().parents[1]
saida = raiz / "figuras"
saida.mkdir(exist_ok=True)
p = json.loads((raiz / "evidencias/piloto.json").read_text(encoding="utf-8"))
fig, ax = plt.subplots(figsize=(9, 3.6), layout="constrained")
valores = [p["rd_linhas"], p["junção_direta_linhas"], p["aih_depois"]]
barras = ax.barh(["RD de origem", "Junção direta", "Integração por hospital e mês"], valores,
                 color=["#175D70", "#A44921", "#175D70"])
ax.invert_yaxis()
ax.bar_label(barras, labels=[format(v, ",").replace(",", ".") for v in valores], padding=5)
ax.set(xlim=(0, max(valores)*1.22), xlabel="Contagem de registros", title="Efeito da estratégia de integração · DF, junho de 2025")
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: format(x, ",.0f").replace(",", ".")))
ax.spines[["right", "top", "left"]].set_visible(False)
fig.savefig(saida / "piloto.png", dpi=170)
plt.close(fig)
fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
ax.axis("off")
ax.set_title("Consulta por estabelecimento · esboço de interface", loc="left", fontsize=16)
def bloco(x,y,w,h,titulo,detalhe):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.006",facecolor="#EDF5F6",edgecolor="#81A6AD"))
    ax.text(x+.02,y+h*.68,titulo,weight="bold",color="#174F5B")
    ax.text(x+.02,y+h*.24,detalhe,fontsize=9)
bloco(.02,.77,.96,.17,"Filtros","Competência   ▾       Estabelecimento   ▾")
bloco(.02,.48,.46,.21,"Produção hospitalar","Registros de AIH e valor aprovado")
bloco(.52,.48,.46,.21,"Estrutura cadastrada","Leitos existentes e leitos SUS")
bloco(.02,.20,.96,.20,"Detalhamento por unidade","Identificação do estabelecimento   |   Produção   |   Estrutura")
ax.text(.02,.07,"Qualidade e rastreabilidade   ›   Fonte, competência e regra do indicador",color="#174F5B")
fig.savefig(saida / "wireframe.png", dpi=170)
