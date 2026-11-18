# Fontes e situação de verificação

Consultas desta entrega: 10/11/2026 (Brasília). Informes são fontes de autoria DATASUS recuperadas em espelho acadêmico, não o servidor original.

- SIH: https://rfsaldanha.github.io/sis/assets/sih/IT_SIHSUS_1603.pdf — informe 2016-03; campos RD, páginas 1–3. Não comprova sozinho vigência integral em 2025.
- CNES: https://rfsaldanha.github.io/sis/assets/cnes/IT_CNES_1706.pdf — informe 2017-06; seção ST e página 20 LT. Cabeçalho físico de 2025 contém campos adicionais; não presumir suas definições.
- Notas SIH: https://tabnet.datasus.gov.br/cgi/sih/Proced_hosp_loc_int_2008.pdf — conceitos de AIHs, internações, valores e limites de permanência.
- Estudo oficial com descrição dos códigos IDENT: https://www.gov.br/planejamento/pt-br/assuntos/planejamento/estrategia-2050-conteudo/Arquivos/eb2050-estudo-perspectivas-demograficas.pdf — confirmação complementar, não substitui manual operacional vigente.
- Conversor: https://github.com/AlertaDengue/pyreaddbc — API dbc2dbf.
- pandas: https://pandas.pydata.org/docs/reference/api/pandas.merge.html — cardinalidade e chaves nulas.
- Streamlit: https://docs.streamlit.io/develop/concepts/app-testing — testes por AppTest.

## Evidência de origem dos dados desta entrega

DBC recebidos em anexos de outubro, recuperados dos ZIPs originais. Hashes comparados ao inventário do piloto anterior. URL e momento do download original permanecem não autenticados. O manifesto registra URLs oficiais previstas separadamente da origem efetiva local.

## Distinção de dicionários

`perfil.json` descreve todos os campos físicos observados (tipo DBF, largura, casas decimais, ausências, distintos). `dicionario_campos_usados.csv` documenta somente os campos usados. Campos não utilizados não foram todos validados semanticamente. Não chamar o perfil de dicionário oficial completo.
