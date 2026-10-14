# F3: covariáveis

## Censo 2022 por setor (`covariates/censo.py`)

- **Fonte:** agregados por setor do IBGE, arquivos nacionais filtrados para a capital. Temas: básico, demografia, cor ou raça, alfabetização, domicílio (partes 1 a 3), renda do responsável (liberada em 2026-05-08) e entorno (faces de quadra, domicílios e moradores). Os dicionários oficiais ficam em `data/external/ibge/censo2022/dicionarios/`.
- **Saída:** `data/processed/covariaveis/setor_censo2022.parquet`, com 27.301 setores e 42 indicadores:
  - população, domicílios e densidades;
  - idade e sexo (homens de 15 a 29 anos, 15 a 24, 0 a 14, 60 ou mais, razão de sexo);
  - cor ou raça (branca, preta, parda, negra, amarela);
  - analfabetismo a partir de 15 anos;
  - tipo de domicílio (apartamento, casa, vila ou condomínio, cortiço, estrutura degradada, improvisados);
  - saneamento (água, esgoto, lixo, banheiro, três ou mais banheiros);
  - renda do responsável (média, mediana, coeficiente de variação);
  - entorno, por fração de faces de quadra com: iluminação pública, pavimentação, calçada, obstáculo na calçada, rampa, bueiro, ponto de ônibus, três ou mais árvores, circulação de ônibus e caminhão, circulação só de pedestres.
- **Supressão:** o IBGE suprime células pequenas ("X"). Quando o setor tem total de moradores publicado, uma contagem suprimida vira 0. Isso não vale para médias e variâncias. Setores sem moradores publicados (622, ou 2,3%) ficam ausentes.
- **Tempo:** variável estática de 2022. A renda só foi liberada em maio de 2026, o que é aceitável numa análise retrospectiva (spec-dados §3.3).

## ITBI: transações imobiliárias (`covariates/itbi.py`)

- **Fonte:** Secretaria da Fazenda, "Guias de ITBI pagas", 21 arquivos anuais de 2006 a set/2026, com abas mensais.
- **Volume:** 2.715.199 transações desde 2006. Cada uma traz SQL, natureza, valor declarado, data, valor venal de referência, financiamento, áreas, uso e padrão.
- **Ligação com o lote:** o SQL de unidade de condomínio é levado ao lote pelo IPTU do mesmo ano, do seguinte (lançamentos) e do anterior. 88,2% das transações caem num lote existente hoje; 99,9% chegam a um setor 2022, pelo lote ou pela quadra fiscal (setor da maioria dos lotes da quadra).
- **Lotes extintos:** transações em lotes que depois somem do cadastro são um sinal de incorporação (compra de casas vizinhas → unificação → prédio). A fração por setor e mês fica em `frac_lote_extinto`.
- **Saídas:** `data/interim/itbi/itbi_lote_mes.parquet` (1,25 milhão de linhas lote × mês) e `itbi_setor_mes.parquet` (1,12 milhão de linhas setor × mês). As medidas são número de transações, valor total, mediana do preço por m² e fração financiada.

| Ano | Transações | Preço/m² mediano (R$) | Fração financiada |
|---|---|---|---|
| 2006 | 112.399 | 758 | 18,5% |
| 2010 | 128.360 | 1.288 | 26,6% |
| 2014 | 100.847 | 2.435 | 25,6% |
| 2018 | 89.797 | 2.974 | 21,3% |
| 2021 | 171.003 | 3.000 | 39,6% |
| 2023 | 172.242 | 2.445 | 41,0% |
| 2025 | 229.510 | 2.287 | 43,2% |
| 2026 (jan–set) | 150.986 | 2.302 | 50,5% |

**Cuidado:** a queda do preço mediano por m² a partir de 2022 coincide com o aumento das compras financiadas. Provavelmente é efeito de composição (mais imóveis pequenos financiados), e não queda real de preços. Nos modelos, convém usar preços relativos ao setor ou ao tipo de imóvel.

## Infraestrutura e equipamentos (`covariates/infra.py`)

- **Fonte:** WFS do GeoSampa. Todas as camadas são fotografias atuais (2026), sem histórico. Camadas grandes são baixadas em páginas de 30 mil feições.
- **Saída:** `data/processed/covariaveis/setor_infra.parquet`, com 18 colunas por setor:
  - distância a estação de metrô, estação de trem (e a menor das duas), terminal e corredor de ônibus, delegacia (pontos), base da PM e da GCM, favela, cortiço, parque, praça, UBS e feira livre;
  - contagem e densidade por km² de pontos de ônibus (22.437) e de pontos de iluminação pública (662.095).
- **Iluminação:** todos os pontos já são LED (carga única de 2026-07-14), então só a densidade varia entre setores. Não há histórico de troca para LED (lacuna já prevista).
- **Endogeneidade:** delegacias e bases da PM e da GCM são instaladas onde há crime. Entram como contexto e ficam marcadas para análise de sensibilidade.
- **Áreas de DP:** a camada `delegacia_policia_civil` são polígonos das áreas de DP, não pontos. Ela não é usada aqui, mas serve para cruzar com a delegacia de circunscrição dos BOs.

## Lacunas registradas

- **Demanda do Metrô:** a fonte pública cobre só as linhas 1, 2, 3 e 15. Faltam a Linha 4, a Linha 5 e a CPTM, e as médias mensais por estação só existem para alguns anos. Um fluxo calculado só com essa parte seria enviesado. Fica para depois, quando houver as linhas privadas e a CPTM.
