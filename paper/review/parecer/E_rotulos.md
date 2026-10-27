# Agente E: rótulos das figuras (pedido do autor; parecer R16)

**Data:** 2026-10-20. **Onde ficam os nomes:** `src/cityomics/viz/names.py`, um só lugar para todas as figuras (Figs. 1–6 e Extended Data). `figdata.GENE_EN`, `figdata.NOMES_MODELO`, `palette.NOMES_GRUPOS_EN` e `figures/rotulos.py` agora só apontam para lá.

**Como os nomes são gerados:**
- **Tipos de lote:**
  - o nome longo vem de `name_en` (`typing._nome`), lido de `tipos_perfil_2025.parquet`;
  - o nome curto vem de `TYPE_SHORT`, que cobre todo o vocabulário de `_nome`, com o sufixo " 2", " 3" preservado.
- **Arquivos de rodadas diferentes:** quando um arquivo do atlas usa um nome de tipo que não está no perfil corrente, `names._Nomes.get` traduz pela mesma lista (`TYPE_PT_EN`). Isso acontece durante a refação.
- **Nada fixo:** nenhum nome de tipo está escrito nos roteiros. A Fig. 4c escolhe as classes por regra:
  - o tipo residencial horizontal com maior padrão baixo;
  - as favelas;
  - o tipo de comércio com maior taxa por km;
  - as estações de trem e metrô.

## 1. Tabela antigo → novo

### 1.1 Classes de célula (rótulo curto; Figs. 2d, 3d, 4, 5d, ED1, ED2, ED7, ED10)

| Antigo | Novo | Nome longo (`name_en`, inalterado) |
|---|---|---|
| low-rise (low) | Low-standard houses | Low-rise residential, low standard |
| low-rise (mid) | Mid-standard houses | Low-rise residential, middle standard |
| low-rise (high) | High-standard houses | Low-rise residential, high standard |
| corner lots | Corner houses | Corner residential |
| mixed res./retail | Houses with shops | Mixed residential and commercial |
| wholesale mixed | Houses with wholesale | Low-rise mixed, wholesale |
| retail (low) | Low-standard shops | Street retail, low standard |
| retail (mid) | Mid-standard shops | Street retail, middle standard |
| high-rise | Mixed-use high-rise | Mid/high-rise, residential and mixed |
| (sem rótulo curto) | Apartment blocks | Mid/high-rise residential |
| (sem rótulo curto) | High-standard high-rise | High-rise, high standard |
| services | Services | Services and facilities |
| industry | Industry | Industry and warehouses |
| vacant | Vacant land | Vacant land |
| favelas / Favelas (FCU) / Favela (census FCU) / Favelas (census FCU) | Favelas (curto); Favelas (census areas) (longo) | — |
| unrecorded / Unrecorded | No cadastral record | — |
| arterials / collectors / local streets | Arterial streets / Collector streets / Local streets | — |
| rail stations / bus terminals | Rail stations / Bus terminals | — |

### 1.2 Famílias de lote (Fig. 1e, Fig. 5d, ED9a)

| Antigo | Novo (longo) | Novo (curto, Fig. 5d) |
|---|---|---|
| Residential, low-rise / Low-rise res. / Low-rise | Low-rise residential | Low-rise housing |
| Residential, high-rise / High-rise res. / High-rise | Mid/high-rise residential | High-rise |
| Residential, high standard / High-standard res. / High-std. | High-standard residential | High-standard |
| Commerce | Commerce and mixed use | Commerce |
| Vacant / green / Vacant | Vacant land | Vacant land |
| Informal / Favela | Favelas | Favelas |
| Unrecorded | No cadastral record | No record |

### 1.3 Atributos dos lotes (Fig. 2b; explorador)

| Coluna | Antigo | Novo |
|---|---|---|
| n_unidades | Units | Units on the lot |
| valor_m2_terreno, valor_m2_construcao | Land value / m², Building value / m² | Land value per m², Building value per m² |
| uso_terreno | Vacant land | Vacant-land use |
| cnpj_bar_restaurante | Bars and restaurants | Bars and restaurants (businesses) |
| cnpj_comercio_varejista | Retail shops | Retail shops (businesses) |
| cnpj_comercio_atacado | Wholesale | Wholesale (businesses) |
| cnpj_financeiro | Banks and finance | Banks and finance (businesses) |
| cnpj_industria | Manufacturing firms | Manufacturing (businesses) |
| cnpj_transporte_armazenagem, cnpj_alojamento, cnpj_educacao_saude, cnpj_construcao_imobiliario, cnpj_servicos_pessoais, cnpj_outros_servicos | (sem sufixo) | mesmo nome + " (businesses)" |
| cnpj_mei | Micro-entrepreneurs (MEI) | Micro-entrepreneurs (businesses) |
| demais (área, pavimentos, testada, usos, padrões, esquina, idade) | — | inalterados |

### 1.4 Relógio (Fig. 4)

| Antigo | Novo |
|---|---|
| T 24, T 25, R 24, R 25 | Phone theft 2024, Phone theft 2025, Phone robbery 2024, Phone robbery 2025 (cor do crime) |
| Contrast H (×100) | Class contrast H (×100) |
| P≤.005 sobre o losango | tabela sob o eixo: "P, events", "P, day blocks", "P, month blocks" (0.005 com zero à esquerda) |
| Deviation from city, 2024 (pp) | Departure from city, 2024 (pp) |
| Theft (r = …) / Robbery (r = …) na legenda | título do subpainel: "Phone theft (pre-specified test) / r = … between years" e "Phone robbery / r = …" |
| (cor por crime) | cor por período: 00–06 h, 06–12 h, 12–18 h, 18–24 h |
| robbery / pedestrians | robbery (model) / pedestrians |
| % of day; Hour | % of the day; Hour (weekdays) |
| Risk per pedestrian (relative) | Robbery per pedestrian (relative) |
| Weekend / weekday (per day) | Weekend / weekday (rate per day) |
| % of the class's robberies | inalterado; título do painel: "Exploratory: phone robbery by hour, per class (model)" |

### 1.5 Modelos e previsão (Fig. 6, ED4, ED5)

| Antigo | Novo |
|---|---|
| NB-GLM | Negative binomial GLM |
| KDE | Kernel density (KDE) |
| GWR (district) | Geographically weighted (GWR) |
| BYM2 | BYM2 spatial model |
| SPDE / LGCP | Log-Gaussian Cox (SPDE) |
| Hawkes | Hawkes (self-exciting) |
| LightGBM (core) / LightGBM (full) | LightGBM (core covariates) / LightGBM (all covariates) |
| GNN | Graph neural network |
| ΔCRPS vs NB-GLM (negative = better) | Difference in CRPS vs negative binomial GLM (negative = better) |
| CRPS skill vs NB-GLM (%) | CRPS skill vs negative binomial GLM (%) |
| where and when / when (within unit) | Between and within units / Within units (month to month) |
| Tract income quintile (predicted/observed) | Tract income quintile (Q1, lowest) × predicted ÷ recorded phone crime |
| Correlation, all sectors × months (where) | Correlation across all tract-months (where) |
| Correlation within sector (when) | Correlation within tracts (when) |
| NB-GLM  ECE 0.026 | Negative binomial GLM, ECE 0.026 |
| ED4: Family; ECE; PAI 1%; Hit 1% (%) | Field of origin; Calibration error (ECE); PAI, 1% of area; Captured, 1% of area (%) (e 5%) |
| Decision model | Decision layer |

### 1.6 Grupos de covariáveis (ED, Sankey)

| Antigo | Novo |
|---|---|
| CPTED | Environmental design (CPTED) |
| Cell-class identity | Cell class (identity) |
| Spatial (district) | District effect |
| Temporal context | Season and trend |
| Other activity / Other CPTED | Other routine activity / Other environmental design |
| Size | Tract size |

### 1.7 Covariáveis do setor e comunicação (ED7, ED8, ED9)

| Antigo | Novo |
|---|---|
| Banks | Banks and finance firms |
| Social vulnerability (IPVS) | Social vulnerability index (IPVS) |
| Income change | Change in income between censuses |
| Young men share | Share of men aged 15–29 |
| Crowding | Residents per dwelling |
| Population growth | Population growth between censuses |
| Street betweenness | Street centrality (betweenness) |
| Dead ends | Share of dead-end streets |
| Night lights (VIIRS) | Night-time light (satellite) |
| Price per m² / Mortgage share | Sale price per m² / Share of financed sales |
| Rail flow / Bus flow / Cash | Rail passengers / Bus passengers / Cash (banks, ATMs) |
| Juxtaview (neighbours) / Paraview (1 km) | Juxtaposed (neighbours) / Para-spatial (1 km) |
| Lee's L (ligand × theft rate) | Lee's L with phone crime rate |
| OOS gain (%); Sig. pairs | Out-of-sample gain (%); Significant pairs |
| OD-2017 flows vs gravity model; OD zone | Origin–destination flows (2017 survey) vs gravity model; survey zone |

### 1.8 Domínios, programas e outros

| Antigo | Novo |
|---|---|
| N1 · vacant + arterials | D1 · Vacant land + arterial streets (Fig. 2e, ED5d, ED7d; o título da legenda da Fig. 2 define D1–Dk) |
| P1 · rail stations + bus terminals; mapas "P1" | Program 1 · Rail stations + bus terminals; mapas "Program 1" |
| ARI between subsamples | Agreement between subsamples (ARI) |
| cov. −13% (à direita da barra) | (cross-term −13%) no rótulo da linha |
| ED3: "(non-MEI, commercial lot)" no título | cabeçalho de linha: "Establishments other than individual micro-entrepreneurs, on commercial or service parcels" |
| ED3: Δ thefts per segment-month | Δ street theft and robbery per segment-month |
| ED2a: grey: share with coordinates | grey numbers: share geocoded |
| ED2c: Crowd factor (people density on the class / mean); pedestrians; people present | Crowd factor (density of people on the class relative to the city mean); Pedestrians (95% CI); People present |
| ED6: ARI; D²; OOS; OAC-style k-means; Ambient population (OD 2017) | subsample agreement (ARI); deviance explained; out-of-sample; Geodemographic k-means (OAC style); Ambient population (2023 travel survey) |

## 2. Nomes de tipo que propomos mudar em `typing._nome` (não editei)

- **Nomes longos que o leitor não decodifica:**
  - "Mid/high-rise, residential and mixed" → "Mid- and high-rise buildings, residential and mixed use".
  - "Low-rise mixed, wholesale" → "Houses with wholesale businesses".
  - "Mixed residential and commercial" → "Houses with shops".
  - "Low-rise residential, low/middle/high standard" → "Low-/middle-/high-standard houses". O curto já faz isso; o longo pode ficar como está.
- **Família com nome contraditório:** `res_vertical_alto` reúne "Low-rise residential, high standard", cuja família aparece como "High-standard residential". Propomos renomear a família para "High-standard housing" ou mover o tipo para `res_horizontal`.
- **Sufixos numéricos:** a tipagem refeita em 2026-10-20 (15 tipos) cria "… 2" e "… 3" que o leitor não distingue. Os dados mostram o que os separa: o atributo de maior excesso padronizado contra os irmãos, calculado sobre `tipos_perfil_2025.parquet`.

| Tipo atual | O que o distingue (z contra os irmãos) | Nome proposto |
|---|---|---|
| Residencial horizontal popular 2 | micro-entrepreneurs (+3.1) | Low-standard houses with a home business |
| Residencial horizontal popular 3 | other services (+3.0) | Low-standard houses with a service business |
| Residencial horizontal médio 2 | micro-entrepreneurs (+3.1) | Middle-standard houses with a home business |
| Residencial horizontal médio 3 | other services (+3.0) | Middle-standard houses with a service business |
| Misto residencial e comercial 2 | bars and restaurants (+4.0), units (+4.0), transport (+4.0) | Multi-unit mixed use with bars and restaurants |
| Terreno vago 2 | corner lot (+3.0), lot area (+1.8) | Vacant corner lots |

**Regra sugerida para `_nome`.** Depois do nome-base, para tipos que repetem o nome, acrescentar o qualificador do atributo de maior excesso, a partir de um dicionário fixo:
- `cnpj_mei` → "with a home business";
- `cnpj_outros_servicos` / `cnpj_servicos_pessoais` → "with a service business";
- `esquina` → "corner";
- `cnpj_bar_restaurante` → "with bars and restaurants";
- e assim por diante.

`TYPE_SHORT` precisa ganhar as formas curtas correspondentes. O sufixo numérico continua funcionando até lá.

## 3. Termos para o glossário de Methods

| Termo (como aparece nas figuras) | Definição proposta |
|---|---|
| Cell class | One of the units whose crime rates are estimated: the parcel types, favelas, parcels without a cadastral record, arterial, collector and local streets, rail stations and bus terminals. |
| Parcel type; family | Cluster of fiscal parcels from cadastral and registry attributes, without crime data; family, a coarser grouping by use and building form (in Fig. 5d, of the cadastral use codes, for transitions over time). |
| Favelas (census areas) | Favela areas of the 2022 census (IBGE *favelas e comunidades urbanas*, FCU), entered as area units with constructed exposure. |
| No cadastral record | Parcels of the lot map without a property-tax (IPTU) record; their attributes are unknown. |
| Low-, mid- and high-standard houses | Low-rise residential types by building standard in the cadastre (a building attribute, not household income). |
| Houses with shops; houses with wholesale | Low-rise parcels with residential and commercial use; the second with wholesale businesses. |
| Mixed-use high-rise | Parcels of three or more floors or four or more units with some commercial use. |
| (businesses) | Count of active establishments of the business registry (CNPJ) linked to the parcel by address. |
| Micro-entrepreneurs | Establishments registered as individual micro-entrepreneurs (MEI), mostly home-based. |
| Tissue; tissue domain (D1–Dk) | The composition of a tract in cell classes; contiguous groups of tracts with similar smoothed composition, named by their most enriched classes. |
| Crime program (Program 1–k) | Component of a non-negative factorization of the tract-by-crime-type matrix, named by its most associated cell classes. |
| Attributed rate (per km, per station) | Expected events per year produced by one km of frontage or street of a class, or by one station, in the Poisson attribution model. |
| Finer-scale check | Spearman correlation between attributed rates and rates obtained by allocating geocoded events to street segments, stations and abutting parcels. |
| Disjoint halves | Random split of geocoded events: rates from one half checked against points of the other. |
| Departure from city profile (pp) | Share of a class's events in a period of the day minus the city's share, in percentage points. |
| Class contrast H | Exposure-weighted chi-square distance between each class's period-of-day profile and the weighted mean profile, summed over classes; the statistic of the clock test (claim C4). |
| Null: events permuted / day blocks / month blocks | Periods permuted between events within districts; or between blocks of events of the same tract and period on the same day or in the same month, kept together. |
| Pedestrians; people present | Hourly density of people walking or cycling on the street, and of people in the tract, from the Origin–Destination household survey 2023 (weekdays). |
| Crowd factor | Pedestrian density on a class relative to the city mean, weighted by when robberies occur. |
| Robbery per pedestrian (risk per pedestrian) | Robbery rate with exposure multiplied by pedestrian density; citywide, robberies divided by summed pedestrian density in each hour, relative to the daily mean. |
| Weekend / weekday ratio | Attributed rate per weekend day divided by the rate per weekday. |
| Reconciled counts; geocoded only; integer imputations | Counts with events lacking coordinates distributed in expectation within district, stratum and month; only events with coordinates; multinomial draws of the same allocation. |
| Noise ceiling | Largest R² a forecast could reach if monthly counts were Poisson around their expectation. |
| Extra-Poisson variance | Month-to-month variance in excess of the mean. |
| Dispersion test; null through the reconciliation | Per-tract χ² test of Poisson dispersion over 12 months; rejection rate expected when Poisson counts are geocoded and reconciled as in production. |
| CRPS; CRPS skill | Continuous ranked probability score (lower is better), against real-valued reconciled counts; 1 − CRPS/CRPS of a reference. |
| Brier score; ECE | Squared error of the probability of at least one event; expected calibration error of that probability. |
| PAI; captured, x% of area | Predictive accuracy index (share of crime captured ÷ share of area); share of crime in the x% of area with the highest forecast density. |
| Ensemble | Stacked combination of the forecasting models. |
| Persistent effect; cross-term | Covariance of a tract's residual beyond composition across years; covariance between composition and residual in the variance split. |
| ARI | Adjusted Rand index between clusterings. |
| Deviance explained (D²) | 1 − deviance of the attribution model / deviance of a constant rate. |
| Cohen's d | Standardized difference of a covariate between a domain and the rest of the city. |
| Knox ratio | Observed / expected pairs of events close in space (≤ 400 m) and time (1–14 days). |
| MISTy views | Intrinsic (own tract), juxtaposed (neighbours) and para-spatial (1 km) predictors of a multiview model. |
| Lee's L | Bivariate spatial association between a crime generator and the crime rate. |
| Colocation quotient; neighbourhood enrichment | Ratio of observed to expected neighbours of type B around type A; z-score of A–B adjacencies against permutations within district and density decile. |
| log₂ enrichment | log₂ of a class's share of a crime type over its mean share across crime types. |

## 4. O que mudou nas figuras (tarefas 2–6)

### Fig. 4: nova ordem pela força da evidência (R16)
- **a:** teste pré-especificado do relógio (C4).
  - Furto de celular primeiro, depois roubo: desvios de cada classe por período, 2024 × 2025, coloridos por período.
  - Contraste H contra três nulos:
    - eventos permutados (`relogio.json`);
    - blocos de dia e blocos de mês (mediana–p95, `ritmo_queda.json`).
  - Os P de cada nulo ficam numa tabela sob o eixo.
- **b:** perfil horário do roubo por classe, com o título "Exploratory: …".
- **c:** roubo × pedestres em quatro classes (OD 2023, `relogio_vs_rua.parquet`, `variante = pe_bici`).
- **d:** risco por pedestre por hora, com a faixa de IC 95% (`risco_pe_bici_ic_*`).
- **e:** razão fim de semana/dia útil com IC 95% (`ritmo_queda.json` → `relogio_ic.fim_de_semana`).
- **f:** roubo por km × por pedestre (OD 2023), com ρ e IC (`presenca_2023.json` → `2023.pe_bici`). Os rótulos dos pontos não se sobrepõem.

### Fig. 6
- Ficaram a (captura), b (teto por escala), c (concentração do excesso) e d (forest).
- O forest foi refeito com o CRPS corrigido; os P ajustados vêm de `prereg/selection_dev.json`.
- O antigo f (auditoria de renda) virou **e**.
- O contraste celular × letal foi para a **ED Fig. 5g**.
- O quadro de confirmação saiu da figura (agora é a Tabela 1).
- Não havia título interno. O título novo, "Month-to-month variation is concentrated and poorly forecast", está em `legends.py` e na legenda proposta abaixo.

### Extended Data
- **ED Fig. 10 (nova), `ed_b.ed10_robustez` → `ed10_robustez`, registrada em `ed.make`:**
  - a: recuperação por simulação: erro relativo por classe, cobertura e ρ;
  - b: metades disjuntas × original;
  - c: ocultação: razão da variância e teto, verdadeiro × recuperado;
  - d: teste de dispersão × nulo calibrado e Poisson puro;
  - e: favelas sob exposições alternativas;
  - f: P do relógio com nulos em blocos.
  - O JSON lido é `data/processed/atlas/fenotipo/identificacao.json`. Sem ele, os painéis a, b e e mostram "identificacao.json pending".
  - No desenvolvimento, usei a variável `CITYOMICS_IDENTIFICACAO_JSON` apontando para o `identificacao_v0.json` do scratchpad.
- **ED Fig. 2c:** fatores de multidão da OD 2023 (`fator_multidao_rua` e `fator_multidao_presenca`), com IC 95% dos pedestres tirado de `presenca_2023/bootstrap.parquet`.
- **ED Fig. 5g:** celular × letal (antigo Fig. 6e).
- **ED Fig. 3:** cabeçalhos de linha (a, todo estabelecimento; b, não MEI em lote comercial ou de serviço) no lugar do sufixo "non-MEI" no título.
- **ED Fig. 6:** os números do multiverso e o "≈4%" deixaram de ser digitados: agora são lidos de `multiverso.parquet`, `selection_dev.json` e do benchmark. A linha "Library size" passou para a OD 2023.
- **ED Figs. 1, 7, 8 e 9:** rótulos novos e ajustes de leiaute.
  - ED1b deixou de cortar os rótulos.
  - ED1a ganhou rótulos nas cinco curvas mais altas, com as cores dos tipos iguais às das Figs. 1 e 2.
  - ED8 deixou de cortar a coluna de status.

### Infraestrutura (só em `figures/` e `src/cityomics/viz/`)
- **`style.save`:**
  - converte eixos log em números simples, porque os expoentes em mathtext saíam com 3,85 pt;
  - fixa em 5 pt as marcas das barras de cor;
  - resultado: todos os PDFs têm corpo mínimo ≥ 5,0 pt, conferido com pypdf.
- **`figdata._cached`:** refaz o cache quando a entrada é mais nova.
  - forest: `selection_dev.json` e `resultados_benchmark_dev.json`;
  - dotplot: `lote_tipos` e `lote_genes`.
  - Os caches de captura, correlação dentro do setor e calibração não têm checagem de dependência.
- **Auxiliares:**
  - `common.row_swatches`: quadradinhos de cor sem sobrepor rótulos;
  - `common.place_labels`: rótulos de pontos sem colisão;
  - `chord.circle`: afasta rótulos que se tocam;
  - `ed.table`: quebra o texto das células.
- **`legends.py`:** Fig. 4, Fig. 6 e todos os Extended Data foram reescritos na numeração do manuscrito, com números lidos dos dados.

## 5. Legendas propostas (inglês; para o coordenador colar no manuscrito)

Os números vêm dos dados de 2026-10-20/21 e devem ser conferidos depois da refação. `figures/legendas_dev.md` gera a versão longa com os números atualizados.

**Fig. 4 | Each class keeps its own daily rhythm.** **a**, Pre-specified test of the class clock (claim C4), phone theft first. Left, departures of each class from the city's share of events in four periods of the day, 2024 against 2025 (dots, class by period; phone theft r = 0.96, phone robbery r = 0.85). Right, class contrast H against three nulls: periods permuted among events within districts (grey; 200 permutations) and among blocks of events from the same tract and period on the same day or in the same month (bars, median to 95th percentile of 999 permutations); P values below the axis (phone theft, P ≤ 0.005 against every null in both years; phone robbery in 2025, P = 0.015 with events but P = 0.15 and 0.46 with day and month blocks). **b**, Exploratory: hourly profile of phone robbery per cell class estimated by the attribution model (2024–2025, events with exact hour). **c**, Weekday robbery (line, model estimate) and pedestrians on the street (grey; Origin–Destination survey 2023) in four classes. **d**, Citywide robbery risk per pedestrian by hour relative to the daily mean (weekdays; shading, 95% interval from 1,000 household resamples of the survey). **e**, Weekend-to-weekday ratio of daily rates of phone theft and phone robbery per class (bars, 95% intervals from 200 district bootstrap resamples). **f**, Robbery per km against robbery per pedestrian across classes (Spearman ρ = 0.79, 95% interval 0.75–0.83).

**Fig. 6 | Month-to-month variation is concentrated and poorly forecast.** **a**, Share of 2025 phone crime captured when flagging the highest-risk tracts, for the ensemble, the historical mean, the share expected if the ensemble's forecasts were exact and an ex-post oracle (all 96 districts). **b**, R² reached by the ensemble (filled) and noise ceiling (open) for variation between and within units and within units only, by spatial and temporal scale (exploration districts). **c**, Cumulative shares of phone crime and of extra-Poisson monthly variance across tracts ranked by count. **d**, Difference in continuous ranked probability score (CRPS, against real-valued reconciled counts) between each method and the negative binomial GLM (bars, 95% district bootstrap intervals; filled, Holm-adjusted P < 0.05 against the best baseline). **e**, Share of flagged area (top 5%) and of recorded phone crime by tract income quintile, with the ratio of predicted to recorded counts.

**Extended Data Fig. 2 | Crime-type panel.** **a**, Events per crime type in exploration tracts (2024–2025) and share geocoded. **b**, Stability across seeds and reconstruction error of crime programs by rank; dashed line, chosen rank. **c**, Density of pedestrians (filled; bars, 95% intervals from 1,000 household resamples) and of people present (open) on each class relative to the city mean, weighted by when robberies occur (Origin–Destination survey 2023, weekdays). **d**, Tissue turnover against month-to-month variability of phone crime within tracts (Spearman ρ = 0.13).

**Extended Data Fig. 3 | Business openings and closures do not change street crime within a year.** Event study on street segments, treated against never-treated segments of the same district and street class (baseline months −12 to −7). **a**, Any establishment. **b**, Establishments other than individual micro-entrepreneurs on commercial or service parcels. Shading, 95% bootstrap intervals; titles, treated segments and effect relative to the baseline.

**Extended Data Fig. 4 | Forecasting benchmark, 2025 (development).** Continuous ranked probability score, log score, Brier score of at least one event, expected calibration error (ECE), predictive accuracy index (PAI, share of crime captured divided by share of area) and share of crime captured at 1% and 5% of the area for every method (tract by month, one month ahead, fitted on 2023–2024).

**Extended Data Fig. 5 | Out-of-sample performance in detail.** **a**, Scores of the finalists. **b**, Monthly skill against the negative binomial GLM. **c**, Tracts flagged in the top 5% of area against the observed top 5% (rasterized). **d**, Skill by tissue domain. **e**, Calibration; ECE, expected calibration error. **f**, Correlation across all tract-months against correlation within tracts. **g**, Skill against the historical mean at district by quarter for phone crime and lethal violence.

**Extended Data Fig. 10 | Robustness of attribution, reconciliation and the clock.** **a**, Recovery of the 2025 class rates of phone crime in 200 simulations from the real exposures with known rates (Poisson counts, district-level risk, tract-level overdispersion, rates permuted among classes): median relative error (bars, ± median absolute relative error; open, beyond ±100%) and coverage of 95% district-bootstrap intervals (50 simulations; dotted line, 95%); legend, median Spearman ρ between true and recovered rates. **b**, Finer-scale check with disjoint halves of geocoded events: rates from a random half against segment-allocated rates of the other half (filled; bars, range of five splits) and the original check with all events (open), across parcel types, for crime types with at least 80% of events geocoded. **c**, Coordinates of geocoded phone-crime events hidden at each stratum's observed missing rate (at random within stratum, more where crime is high, more on residential frontage; 10 replicates) and reconciled: within-tract monthly variance of recovered relative to true counts (left) and within-tract noise ceiling of true (open) and recovered (filled) counts (right). **d**, Share of tracts in which a per-tract dispersion test rejects Poisson noise at the 5% level, observed (diamonds) and under nulls simulated through the same geocoding and reconciliation (open; 200 replicates) or as pure Poisson counts (grey), for reconciled counts, integer imputations and geocoded events only. **e**, Log₂ enrichment of crime types in favelas under alternative favela exposures (bars, 95% district-bootstrap intervals for the current exposure; legend, median Spearman ρ of class shares against the current exposure). **f**, Permutation P of the class contrast under the article's null (events permuted between periods within districts) and under nulls that permute blocks of events from the same tract and period on the same day or in the same month; open, at the permutation floor; dashed line, P = 0.05.

**Remissões no texto do manuscrito que mudam com a nova Fig. 4 e a nova Fig. 6** (não editei o manuscrito):
- **Linha 36:**
  - "(Fig. 4a)" passa a "(Fig. 4b)";
  - "(r = 0.93; Fig. 4d)" passa a "(…; Fig. 4a)";
  - "(Fig. 4b)", sobre o pico pré-amanhecer, passa a "(Fig. 4b,c)";
  - os valores de r e P mudaram: r = 0.96 e 0.85 agora. O P do roubo em 2025 com nulo de eventos agora é 0.015, mas 0.15 e 0.46 com os nulos em blocos, o que reforça "phone robbery did not replicate".
- **Linha 38:** "(4.2–5.1; Fig. 4c)" passa a "Fig. 4d".
- **Linha 54:** o teste de dispersão contra o nulo calibrado agora aparece na ED Fig. 10d. Sugerimos "(Fig. 6c and Extended Data Fig. 10d)".
- **Linha 84:** "Fig. 6a,d,e,f" passa a "Fig. 6a,d,e".
- **Linha 76 (limitações):** a metade disjunta, os nulos em blocos e as exposições das favelas agora estão na ED Fig. 10b, f, e. A frase "Several robustness checks remain" deve ser revista quando os números finais chegarem.
- **Methods (linha 112):** acrescentar os nulos em blocos (999 permutações, dia e mês).

## 6. O que depende dos dados finais

- **Nomes e número de tipos:**
  - com a tipagem de 15 tipos, aparecem "Low-standard houses 2/3" etc.; ver a proposta da seção 2;
  - durante a refação, arquivos do atlas de rodadas diferentes usam nomes de tipo antigos. Os rótulos são traduzidos pelo vocabulário, mas as cores e a ordem só ficam corretas quando todo o atlas usar a mesma tipagem.
- **Classes escolhidas por regra:** as quatro classes da Fig. 4c, os rótulos dos pontos da Fig. 4f e as cinco curvas rotuladas da ED1a saem dos dados e podem mudar.
- **`ritmo_queda.json`:** tem de ser refeito depois de `relogio.json`. Hoje o H dos blocos difere do H do relógio (0,114 contra 0,137 no furto de 2024), e `fig4.py` imprime um aviso quando isso acontece.
- **OD 2023:** `presenca_2023/*` usa os nomes de classe da tipagem anterior e precisa ser refeita depois do atlas.
- **`identificacao.json`:** é final só em `fenotipo/`. O v0 não tem `celular_furto` em `metades.testados` (cobertura abaixo de 80%) nem a alternativa `indicador_setor` das favelas; o código lida com as duas ausências.
- **`legends.py`, legendas das Figs. 3 e 5 (não reescritas):** ainda citam classes por nome, como 'Comércio de rua médio', 'Vertical residencial e misto' e 'Residencial horizontal popular'. Com a nova tipagem darão NaN e precisam passar a regras como as da Fig. 4.
- **ED Fig. 8:** o status "not run: 2017 survey used only for the ambient population" vem de `comunicacao/multiverso.parquet`, que é do atlas, e está desatualizado depois da troca para a OD 2023.
- **Comando para regenerar:** `OMP_NUM_THREADS=3 python -m cityomics.cli figures`. Sem `--only`, o comando também refaz `figures/legendas_dev.md`. O cache do forest se refaz sozinho quando `selection_dev.json` ou o benchmark mudam.
