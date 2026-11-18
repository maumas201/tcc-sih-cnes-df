# Delimitação para orientação

**Título proposto**  
Desenvolvimento e avaliação técnica de um protótipo de Business Intelligence para integrar produção hospitalar e leitos cadastrados do SUS no Distrito Federal

**Problema de pesquisa**  
O acompanhamento conjunto da produção hospitalar e da estrutura cadastrada exige compatibilizar a unidade de observação e a referência temporal das fontes. O SIH/SUS registra produção administrativa por AIH. O CNES descreve estabelecimentos e leitos cadastrados por competência. Um estabelecimento pode apresentar diversas categorias de leitos no mesmo mês. Associar cada registro de produção a cada categoria repete os valores da AIH e compromete os totais apresentados em um painel. O problema de Sistemas de Informação consiste em especificar uma integração que preserve as medidas de origem e permita verificar o caminho entre arquivo, regra e indicador.

**Fundamento e evidência**  
A SES-DF descreve a relação entre cadastro e produção e a importância da competência na consistência do faturamento. O DATASUS distingue o mês de processamento das datas de atendimento e define as medidas de AIH. Kimball descreve o risco de unir medidas detalhadas de duas tabelas e recomenda agregá-las separadamente em dimensões comuns. O projeto de pesquisa anterior já mobilizava Kimball na seção 3.3.2. A quantificação da multiplicação é um resultado experimental dos autores para junho de 2025. A data do download original dos arquivos permanece sem comprovação documental. [SES-DF](https://info.saude.df.gov.br/sala-de-situacao/painel-infosaude-cnes-x-sistemas-de-producao/) · [DATASUS](https://tabnet.datasus.gov.br/cgi/sih/Proced_hosp_loc_int_2008.pdf) · [Kimball Group](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/multipass-sql/) · [Experimento](../evidencias/piloto.json). Acesso às fontes web em 18 nov. 2026.

**Pergunta**  
Como integrar os registros de produção hospitalar do SIH/SUS aos dados de estabelecimentos e leitos do CNES em um protótipo de BI para o Distrito Federal, preservando os totais de origem e permitindo rastrear os indicadores por estabelecimento e competência?

**Objetivo geral**  
Desenvolver, documentar e avaliar tecnicamente um protótipo de Business Intelligence que integre dados públicos do SIH/SUS e do CNES para consulta de indicadores de produção hospitalar e leitos cadastrados no Distrito Federal, a partir de requisitos derivados de documentos e organizados com personas.

| Subpergunta | Objetivo específico | Evidência esperada |
|---|---|---|
| Que consultas se justificam pelas atribuições documentadas? | Especificar personas, tarefas e requisitos documentais. | Matriz documento–requisito–cenário |
| Em que unidade os totais são preservados? | Implementar a integração por estabelecimento e competência e comparar as estratégias. | Contagens e valores em centavos antes e depois |
| Como conferir um indicador exibido? | Implementar consultas agregadas e registrar fórmulas, fontes e critérios de avaliação. | Manifesto, casos de teste, saídas do painel e comparação externa quando equivalente |

**Delimitação**  
Piloto de junho de 2025, segundo local de internação no DF e competência de processamento. O universo analítico parte das unidades com produção no RD. Hospitais conveniados também podem produzir para o SUS. Restringir a gestão ou propriedade pública exigiria filtro cadastral justificado. Os arquivos de entrada incluem registros administrativos individuais. A apresentação e os arquivos de resultados para divulgação são agregados. A avaliação mede propriedades computacionais. Adoção, satisfação e impacto decisório exigiriam outro desenho de estudo.

## Decisões para a reunião

1. A expressão “estabelecimentos com produção hospitalar SUS no DF” corresponde ao recorte pretendido ou há exigência de selecionar unidades de natureza jurídica pública?
2. O perfil primário de análise de informação e o perfil secundário de coordenação hospitalar, delimitados por documentos, atendem à orientação sobre personas?
3. O título, a pergunta e os critérios de conservação, cobertura e rastreabilidade permitem julgar o artefato dentro da proposta de SI?
4. Uma competência atende à demonstração, com a generalização temporal registrada como limitação? Qual o prazo de entrega do texto anterior à banca de 7/12?
5. Qual versão do modelo de SI rege a entrega e onde registrar a contribuição de ferramentas de IA na redação e no código?
