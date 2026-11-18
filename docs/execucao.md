# Método, arquitetura e primeira execução

## Do problema ao artefato

A DSRM organiza a pesquisa em seis atividades. A identificação do problema corresponde ao risco de repetir produção na integração. A definição dos objetivos traduz esse risco em critérios de conservação e rastreabilidade. O projeto e o desenvolvimento produzem requisitos, pipeline e painel. A demonstração aplica o artefato a junho de 2025. A avaliação compara as estratégias de junção, verifica contratos de dados e executa cenários técnicos. A comunicação reúne a monografia, o repositório e a defesa. [Peffers et al., A Design Science Research Methodology for Information Systems Research](https://doi.org/10.2753/MIS0742-1222240302).

| CRISP-DM adaptado | Ação no projeto | Produto inspecionável |
|---|---|---|
| Entendimento do negócio | Delimitar o público, a competência e a pergunta de monitoramento | Documento de escopo e personas |
| Entendimento dos dados | Identificar arquivos, campos, tipos físicos e códigos | Manifesto, perfil e dicionário |
| Preparação | Padronizar chaves, distinguir AIHs normais e de prorrogação e converter valores em centavos | Arquivos preparados por fonte |
| Modelagem | Modelar fatos e dimensões no grão correto | Uma linha por CNES e competência com produção |
| Avaliação | Confrontar contagens, valores e registros sem correspondência | piloto.json, testes e comparação com TABNET |
| Disponibilização | Expor indicadores agregados, filtros e evidências | Painel Streamlit e README |

A modelagem é analítica e descritiva. A série de um mês permite testar integração e conservação. Tendências e desempenho gerencial exigem evidências adicionais.

## Camadas e funções

1. **Origem.** ingest recebe ano/mês, determina os endereços do DATASUS pelo nome do arquivo e grava os DBC em raw. O SHA-256 identifica a sequência de bytes: repetir a cópia do mesmo arquivo deve gerar o mesmo hash. O manifesto registra origem efetiva, horário UTC, tamanho e endereço esperado.
2. **Conversão.** profile verifica os hashes, descompacta DBC em DBF, lê as colunas e escreve Parquet. O perfil identifica campos ausentes e tipos físicos. A interpretação de cada campo usado está no [dicionário](dicionario_campos_usados.csv).
3. **Preparação.** prepare verifica a competência interna, trata o CNES como código de texto e converte valores monetários em centavos. Isso preserva zeros à esquerda e permite comparar somas exatamente.
4. **Integração.** production agrupa registros RD; beds agrega categorias de leitos do LT. integrate une os dois resumos e confere a correspondência em ST. A opção validate="one_to_one" exige uma única linha por chave de cada lado. A junção à esquerda preserva a produção inclusive quando a informação cadastral está ausente.
5. **Consulta.** app.py lê resultados para consulta por unidade. A média de permanência usa a população de AIHs normais definida em core.py. AIH por leito SUS relaciona produção administrativa e capacidade cadastrada. O estudo não dispõe da série diária de leitos operacionais e pacientes-dia para estimar ocupação ou giro.

**Exemplo conceitual.** Imagine uma AIH e duas categorias de leito do mesmo hospital. A junção direta gera duas linhas contendo o mesmo valor da AIH. Ao somar as categorias primeiro, o hospital passa a ter uma única linha de estrutura para receber a produção. No piloto, a soma da coluna de contagens após a integração é comparável ao número original de registros. A quantidade de linhas da tabela final corresponde aos estabelecimentos com produção naquele mês.

## Execução no Windows

Na raiz do projeto, em PowerShell, preparar Python 3.12:

```powershell
py -3.12 -m venv .venv
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -r requirements.txt
& $py -m pytest -q tests
```

Para uma aquisição nova, escolher uma pasta de execução inédita. O comando requer conectividade FTP com o DATASUS.

```powershell
& $py -m tccbi.pipeline ingest --competence 202506 --run runs/junho
```

Para reproduzir com cópias já existentes, colocar RDDF2506.dbc, STDF2506.dbc e LTDF2506.dbc em dados_originais e usar o comando abaixo no lugar da aquisição por rede. O campo obtido_utc passa a registrar o instante da cópia local. O manifesto original do piloto identifica essa modalidade. A competência 202506 indica o período do dado e é independente da data da aquisição.

```powershell
& $py -m tccbi.pipeline ingest --competence 202506 --source-dir dados_originais --run runs/junho
```

Continuar com a pasta da aquisição concluída:

```powershell
& $py -m tccbi.pipeline profile --run runs/junho
& $py -m tccbi.pipeline prepare --run runs/junho
& $py -m tccbi.pipeline pilot --run runs/junho
& $py -m tccbi.pipeline build --run runs/junho
& $py -m tccbi.report --run runs/junho --output runs/junho/relatorio
$env:TCC_RUN = "runs/junho"
& $py -m streamlit run app.py
```

Para reproduzir o experimento nos DBFs correspondentes aos hashes do piloto, a partir da raiz:

```powershell
& $py -m scripts.reproduzir_dbf runs/junho
& $py scripts/conferir_dbf.py runs/junho/converted
```

O primeiro comando confere hashes dos DBC e DBF e recalcula a integração. O segundo faz uma contraprova independente. Para cada hospital e mês, multiplica a quantidade de linhas RD pela quantidade de linhas LT, usando um como multiplicador se não houver correspondência na junção à esquerda. A soma desses produtos prevê quantas linhas a junção direta produziria.

## Critérios e interpretação

| Verificação | Critério | Evidência ou estado |
|---|---|---|
| Contagem e valor conservados | Diferença zero entre RD e resultado integrado em registros e centavos | Reproduzido nos DBF em 18/11/2026 |
| Contraprova da multiplicação | Cálculo independente igual à saída da junção direta | Reproduzido nos mesmos DBF |
| Origem | Cada entrada identificada por nome, competência, bytes, hash, modalidade e horário real da operação | Manifesto de cópia local disponível; aquisição oficial independente ainda pendente |
| Correspondência | Publicar quanto da produção encontra cadastro e quanto ficou sem par; investigar qualquer perda | Contagens em piloto.json. O universo CNES é mais amplo que o da produção RD |
| Referência externa | Comparar apenas UF, local de internação, competência de processamento, seleção de AIH e definição monetária equivalentes. Registrar consulta, data, diferença absoluta e relativa; com denominador zero, indicar razão indefinida | Conciliação TABNET pendente |
| Interface | Executar os cenários descritos na matriz e identificar falhas por requisito | Testes de interface em tests/. Aceitação pelos profissionais não foi medida |

Para regenerar as figuras do README, instalar matplotlib no ambiente e executar `python scripts/figuras.py` com o mesmo interpretador. O gráfico lê a evidência do piloto. O wireframe contém apenas campos e rótulos de interface.

## Marcos propostos até a banca

18–22/11: parecer da orientação sobre escopo e personas, confirmação do modelo e nova aquisição documentada. 23–27/11: fechar indicadores e denominadores, executar testes e conciliar com TABNET. 28/11–02/12: consolidar texto, tabelas e figuras. 03–06/12: revisão com a orientadora e ensaio. 07/12: banca. Ajustar a entrega do texto ao prazo institucional comunicado pela orientação. Em caso de redução de escopo, priorizar o piloto verificável e adiar telas e indicadores acessórios.
