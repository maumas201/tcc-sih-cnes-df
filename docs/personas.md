# Público pretendido, tarefas e requisitos

O público primário compreende profissionais de informação e planejamento que acompanham a produção hospitalar SUS no DF por unidade e competência. Gestores de unidades com atribuição de monitorar indicadores constituem um público secundário. A SES-DF e o DATASUS são instituições relacionadas ao contexto e às fontes. Nenhum desses vínculos implica participação na pesquisa.

O Caderno AGL Hospitalar descreve atribuições do gestor de unidade contratualizada e consultas de indicadores por mês e unidade, inclusive nas orientações das páginas 85–87. A página CNES × Sistemas de Produção descreve funções de cadastramento e a consistência por competência. Os documentos descrevem trabalho institucional. As fichas abaixo traduzem esse trabalho em cenários hipotéticos de projeto. A construção por papel organiza decisões de design e tem alcance limitado para prever comportamento individual. [Caderno hospitalar SES-DF](https://info.saude.df.gov.br/wp-content/uploads/2025/06/Caderno-de-Orientacoes-AGL-Hospitalar-2025.pdf) · [CNES e produção](https://info.saude.df.gov.br/sala-de-situacao/painel-infosaude-cnes-x-sistemas-de-producao/) · [Pruitt e Grudin, Personas: Practice and Theory](https://www.microsoft.com/en-us/research/publication/personas-practice-theory/). Acesso em 18 nov. 2026.

| Atributo | P1 · Analista de informação hospitalar | P2 · Coordenador de unidade hospitalar |
|---|---|---|
| Papel | Perfil hipotético que reúne tarefas de consulta e conferência descritas nos dois documentos | Perfil hipotético inspirado nas atribuições do gestor de unidade no Caderno |
| Contexto documentado | Cruzamento de informações cadastrais e produção por competência (SES-DF) | Acompanhamento de indicadores hospitalares por mês e unidade (Caderno) |
| Objetivo proposto | Explicar a composição do total e recuperar o arquivo de origem | Consultar produção e estrutura cadastrada da unidade no período |
| Situação de uso suposta | Ao encontrar divergência, examina população, competência e regra de cálculo | Antes de uma reunião, seleciona a unidade e examina as medidas disponíveis |
| Risco analítico identificado no projeto | Uma junção repete valores monetários | Leitos cadastrados podem ser interpretados como disponibilidade diária |
| Critério técnico proposto | Recuperar o total original em centavos e a identidade do arquivo | Ver o período, o denominador e a indicação de medida incalculável |
| Limite de evidência | Frequência de uso e preferência de interface desconhecidas | Aceitação e utilidade percebida desconhecidas |

| Persona e fundamento | Requisito proposto | Implementação | Cenário e evidência |
|---|---|---|---|
| P1 · consistência cadastral por competência | R1. Relacionar produção e leitos no mesmo estabelecimento e mês | production, beds e integrate em core.py | Conferir contagem e soma em centavos antes/depois. Saída em piloto.json |
| P1 · conferência de produção | R2. Identificar origem e versão de entrada | ingest e verify_inputs em pipeline.py | Alterar cópia de teste deve interromper processamento. Teste em test_pipeline.py |
| P2 · consulta por unidade no Caderno | R3. Filtrar a unidade e identificar período | Filtros em app.py | Comparar total selecionado com agregado da unidade. Teste de interface e conferência manual técnica |
| P2 · leitura de capacidade (hipótese do projeto) | R4. Distinguir capacidade cadastrada e uso efetivo | Razão AIH/leito cadastrado e tratamento de denominador ausente ou zero | Testar ausência de LT e exibir “Não calculável”. Testes em tests/ |

As personas determinam as consultas que o protótipo deve oferecer. O teste verifica se a consulta funciona para a situação especificada. Uma afirmação de que um gestor usaria a ferramenta ultrapassaria os dados do estudo.
