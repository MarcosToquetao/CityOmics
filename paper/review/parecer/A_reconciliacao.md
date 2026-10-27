# Agente A: reconciliação, ruído e previsão (R1, R2, R4 [ocultação], R8)

**Data:** 2026-10-20. **Módulo:** `src/cityomics/atlas/reconciliacao.py` (`run(log=print)`). **Testes:** `tests/test_parecer_reconciliacao.py` (18 passam). **Saída:** `data/processed/atlas/fenotipo/reconciliacao.json` (agregados) e `reconciliacao_imputacoes.parquet` (setor × mês, local).

**Recorte:** 77 distritos de exploração (21.331 setores), de 2022 a 2025, sem nenhum arquivo de 2026. A única exceção é a repontuação do CRPS nos 96 distritos, pedida pelo coordenador porque é o escopo do número publicado. Ela usa só as previsões já gravadas do benchmark, e nada do atlas toca o cofre.

**Conferência:** a reconciliação vetorizada reproduz `celular_setor_mes.parquet` (diferença máxima 7 × 10⁻¹⁵), com 121.434 eventos em 2025, dos quais 100.275 geocodificados (17,4% reconciliados). Em 2025, 65% dos setor-meses têm contagem fracionária e 48% ficam entre 0 e 1.

**Reprodução:** `OMP_NUM_THREADS=4 python -c "from cityomics.atlas import reconciliacao as rc; rc.run()"`. Leva cerca de 17 minutos, com a máquina compartilhada, e chega a 3,9 GB de pico. As sementes são fixas.

---

## ⚠ Destaque: o CRPS do benchmark não é o CRPS de y real. Isso afeta uma métrica pré-registrada (emenda A6)

**O problema.** `eval/scores.crps_nb` calcula Σₖ (F(k) − 1{k ≥ y})². É a fórmula escrita no §5.3 do pré-registro e fixada pela emenda A6 como "CRPS against real-valued y". Com y fracionário, essa soma dá o CRPS de **⌈y⌉**, não o de y.

O CRPS correto é ∫ (F(x) − 1{x ≥ y})² dx. No intervalo [j, j + 1) que contém y, o termo vale (y − j)·F(j)² + (j + 1 − y)·(F(j) − 1)². A fórmula registrada usa F(j)² no intervalo inteiro. O resultado correto é a interpolação linear entre os CRPS de ⌊y⌋ e de ⌈y⌉.

**Como foi conferido.** Contra a integral numérica e contra E|X − y| − ½E|X − X′| por Monte Carlo (bloco `crps_verificacao` do JSON). Um exemplo: com μ = 0,5, φ = 3 e y = 0,03, a amostragem dá 0,154, a integral e `crps_nb_real` dão 0,156 e a produção dá 0,407, igual ao CRPS de y = 1. Com y inteiro, as três versões coincidem. Há testes para os dois lados.

**Consequência.** Como 48% dos setor-meses têm y entre 0 e 1, a métrica da produção trata quase metade das células sem crime como se tivessem um evento. Isso favorece modelos que superestimam P(y ≥ 1).

Repontuação das previsões gravadas de 2025, 96 distritos, contra o GLM (bootstrap por distrito, 2.000 reamostras):

| | CRPS da produção (⌈y⌉) | CRPS de y real (correto) | y arredondado |
|---|---|---|---|
| CRPS médio do GLM | 0,619 | 0,253 | 0,242 |
| GNN − GLM | **−0,025 (−0,034 a −0,016), −4,0%** (o número publicado) | −0,011 (−0,017 a −0,007), −4,5% | −0,010 (−0,016 a −0,006), −4,2% |
| Melhor modelo único | GNN | **LightGBM núcleo:** −0,012 (−0,018 a −0,008), −4,9% | LightGBM núcleo: −0,012 (−0,017 a −0,008), −4,9% |
| Ensemble − GLM | −0,019 (−0,029 a −0,011), −3,1% | **−0,016 (−0,023 a −0,011), −6,4%** | −0,016 (−0,023 a −0,010), −6,5% |
| Hawkes − GLM | −0,019 (melhor que o GLM) | **+0,009** (0,007 a 0,011; pior) | +0,010 |
| LightGBM sem crime − GLM | −0,020 (melhor) | **+0,013** (0,006 a 0,020; pior) | +0,013 |
| Média histórica − GLM | 0,000 (−0,002 a 0,002) | +0,004 (0,002 a 0,006; pior) | +0,004 |
| Melhor "outras áreas" (seleção do H1a) | GNN | **ensemble** | ensemble |
| H1a de desenvolvimento (Holm com H1b, p = 0,192) | apoia, p_adj = 0,001 | apoia, p_adj = 0,001 | apoia, p_adj = 0,001 |

Nos 77 distritos de exploração o quadro é o mesmo. Na produção, o GNN fica 3,4% abaixo do GLM. Com o CRPS correto, o ensemble fica 6,0% abaixo e o LightGBM núcleo 4,4%.

**O que muda.**
- **O ranking muda.** Com o CRPS correto, o ensemble passa a primeiro e o LightGBM núcleo vira o melhor modelo único. O GNN cai para o terceiro lugar. Hawkes e LightGBM sem crime trocam de lado: passam a ser piores que o GLM.
- **A diferença contra o GLM muda pouco em termos relativos** (4–5% no melhor modelo único), mas o valor absoluto cai de −0,025 para −0,012, porque o CRPS médio cai de 0,62 para 0,25.
- **O H1a de desenvolvimento continua apoiado.** Mas **o modelo selecionado para o H1 muda**: de GNN para ensemble em `selection_dev.json`. `prereg/selection.json` hoje aponta `lgbm_sem_crime`, que vem de outra rodada (VIIRS, não repontuada aqui). Nas previsões de desenvolvimento, esse modelo fica em 11º lugar e é pior que o GLM.
- **As métricas operacionais não mudam.** Captura e PAI não usam o CRPS. O log score usa rint(y) e o Brier usa y ≥ 0,5, como documentado.

**Ação do autor (antes de abrir o cofre).**
- (1) Emenda datada que corrija a fórmula da A6 (CRPS de y real pela interpolação, ou CRPS sobre y arredondado). Sem ela, o H1 de 2026 será avaliado com uma métrica que não mede o que o texto diz.
- (2) Corrigir `scores.crps_nb` (eu não editei, pela regra 4). O teste `test_crps_real_valued_observation_is_between_neighbors_and_nonnegative` não pega o erro, porque aceita valor igual ao do vizinho.
- (3) Refazer `select_run`, `selection_dev.json`, a Fig. 6d e os Extended Data 4 e 5.
- (4) Repontuar também `pred_viirs_*` antes do FREEZE.
- (5) Corrigir o texto (frase proposta na tarefa 5).

---

## 1. Inventário: que contagem cada resultado usa (R2)

| Resultado do manuscrito | Contagem | Onde (arquivo / função) |
|---|---|---|
| Atribuição do celular 2025 (λ, D², IC bootstrap, efeito de distrito) | n_total reconciliado, fracionário | `atlas/attribution.py` `crime_setor` → `run`; `atlas/robustez.py` `efeito_distrito` |
| Checagem em escala fina (ρ = 0,93; mediana 0,85) | geocodificados, inteiros | `attribution.point_validation`; `fenotipo.assinaturas` (validação) |
| Perfis dos 15 crimes, enriquecimento, programas NMF, perfis com distrito | n_total por fenótipo | `fenotipo.alvos` → `fenotipo_setor_ano.parquet`; `fenotipo.assinaturas`, `programas`; `robustez.efeito_distrito` |
| Relógio: λ por período, contraste H, permutação, réplica, perfil horário, fim de semana | **só geocodificados** (`cd_setor` não nulo), inteiros | `fenotipo._eventos_relogio`, `relogio`, `_horas`, `_fim_de_semana` |
| Relógio sem modelo (16% entre 4h e 6h) | geocodificados com hora exata | `robustez.relogio_bruto` |
| Risco por pedestre, horário | geocodificados | `atlas/presenca.py` `_crime` |
| R² fora da amostra e ICC (Fig. 5a) | n_total: alvo de 2025 **e** média histórica 2022–2024 reconciliada | `atlas/variance.py` `frame`, `icc` |
| Persistência (42/48/−13; 18/58; defasagem 3 = 0,63) | n_total; sensibilidade com n_geo | `memoria.contagens`, `decompoe`; `robustez.persistencia_geocodificada` |
| Queda 2022→2025 e razões relativas | n_total | `fenotipo.queda`; `robustez.queda_por_desfecho` |
| Estudo de evento (aberturas e fechamentos) | geocodificados | `atlas/perturbacao.py` |
| Teto de ruído e R² por escala | n_total (y de `pred_dev_eval`) | `previsibilidade.run`, `teto_sem_modelo`, `medidas` |
| Teste de dispersão (4%, 14%; 7% geocodificado) | n_total; sensibilidade com n_geo | `previsibilidade.dispersao` |
| Escala do excesso (88% contra 86%) | n_total | `robustez.escala_do_excesso` |
| Poder do teste | Poisson-gama simulado, inteiro | `robustez.poder_dispersao` |
| Benchmark: alvo de ajuste e de avaliação | n_total | `features/table.py` (y = n_total) |
| Benchmark: histórico usado como preditor | **geocodificados do setor ÷ cobertura do distrito**, as-of; não é o reconciliado | `features/history.py` (`h_int_*`); média histórica = `h_int_s12/12` |
| Escores | CRPS = `scores.crps_nb` (com y fracionário dá o CRPS de ⌈y⌉, ver o destaque); log score em rint(y); Brier com 1{y ≥ 0,5}; φ ajustado em rint(y) | `eval/scores.py`, `eval/harness.py`, `models/select_run.py` |
| Captura, PAI (Fig. 6a) | n_total (as curvas também têm n_geo) | `viz/figdata.capture_curves`; `select_run.in_hotspot` |
| Auditoria de renda | n_total | `eval/fairness.py` |
| Confirmação C1, C3 e C5 / C2 e C4 | n_total / geocodificados | `atlas/confirmacao.py` |

**Duas correções para Methods.** O texto diz que "Attribution uses reconciled counts; the finer-scale check, the clock's model-free count and the geocoded-only sensitivities use geocoded events". Falta o resto: **todo o relógio** (o modelo por período, a permutação, o perfil horário e o fim de semana), o risco por pedestre e o estudo de evento também usam só eventos geocodificados. E o histórico do benchmark não é reconciliado: é o geocodificado do setor dividido pela cobertura do distrito.

---

## 2. Imputação multinomial da reconciliação (R2)

**Pergunta.** Os resultados que usam n_total dependem de tratar a alocação esperada como contagem observada?

**Método.** `reconcile_draw` / `reparte` copiam a reconciliação de produção: mesmas frações, α = 1, janela de 12 meses e trilhos só em setores a até 250 m de estação. A diferença é que os u eventos de cada distrito × estrato × mês são repartidos por sorteio multinomial. A média dos sorteios é a produção e o total do distrito por mês é preservado (ambos testados). Foram feitas M = 20 imputações para 2022–2025. Cada análise foi refeita como na produção. Os intervalos são os percentis 2,5–97,5 entre imputações.

| Medida | Produção (esperado) | Imputações, média [2,5–97,5] | Só geocodificado |
|---|---|---|---|
| (a) D² da composição, 2025 | 0,338 | 0,336 [0,333–0,339] | 0,281 |
| (a) Spearman de λ com a produção (19 classes) | 1 | 1,000 [0,997–1,000] | 0,989 |
| (a) λ estações (por estação e ano) | 87,0 | 87,1 [86,5–87,7] | 45,3 |
| (a) λ comércio médio (por km) | 70,5 | 70,5 [69,8–71,0] | 57,4 |
| (a) largura do intervalo de imputação ÷ IC bootstrap | | mediana 0,04 (máximo 0,14) | |
| (b) composição / persistente / transitória / termo cruzado | 0,421 / 0,478 / 0,233 / −0,131 | 0,409 / 0,465 [0,464–0,466] / 0,251 / −0,125 | 0,395 / 0,457 / 0,261 / −0,112 |
| (b) setores com ≥ 10 esperados: composição / persistente | 0,185 / 0,583 | 0,180 / 0,575 [0,573–0,577] | 0,166 / 0,595 |
| (b) correlação do resíduo na defasagem 3 | 0,633 | 0,617 [0,615–0,619] | 0,619 |
| (c) teto entre + dentro (setor × mês 2025) | 0,922 | 0,923 [0,923–0,924] | 0,882 |
| (c) R² do ensemble entre + dentro (fração do teto) | 0,802 (0,870) | 0,794 [0,791–0,796] (0,860) | 0,593 (0,672)* |
| (c) teto dentro do setor | 0,557 | 0,583 [0,580–0,587] | 0,582 |
| (c) R² do ensemble dentro do setor | 0,018 | 0,017 [0,015–0,020] | 0,013 |
| (d) rejeita Poisson, setores com ≥ 1 evento | 3,9% (16.432 setores) | 6,5% [6,3–6,7] | 6,8% (13.724) |
| (d) rejeita Poisson, setores com ≥ 1 evento/mês | 14,2% (1.734) | 17,7% [16,7–18,8] | 19,4% (1.562) |
| Fig. 5a: R² fora da amostra, **média histórica** | 0,484 | **0,385** [0,382–0,387] (5 imputações) | 0,369 |
| Fig. 5a: R² fora da amostra, tecido / tecido + covariáveis | 0,251 / 0,308 | 0,235 / 0,284 | 0,232 / 0,280 |

\* Previsões não reescaladas para os geocodificados. Serve só de referência.

**Implicação.**
- **A incerteza de alocação é desprezível para as taxas de classe** (4% da largura do IC por distrito) e para a persistência (46–48%).
- O só-geocodificado não é um teste neutro: a taxa das estações cai pela metade porque 81% dos eventos do estrato trilhos não têm coordenada.
- **A alocação esperada suaviza o mês a mês.** O teto dentro do setor sobe de 0,557 para 0,583 e a rejeição do Poisson de 3,9% para 6,5%.
- **A alocação também infla o histórico na Fig. 5a.** O R² da média histórica cai de 0,48 para 0,39 com contagens inteiras, porque as frações seguem o passado geocodificado de cada setor. O histórico continua à frente do tecido, mas a margem sobre "tecido + covariáveis" cai de 0,18 para 0,10.

**Frases propostas.**
- Results, Fig. 5a: "…against 0.48 for the tract's historical mean (0.39 when events without coordinates were imputed as integer counts rather than allocated in expectation)."
- Methods (Units and reconciliation): "Because reconciled counts are expectations, we propagated allocation uncertainty with 20 multinomial imputations that redistribute each district–stratum–month total with the same shares. Class rates (median imputation interval 4% of the district-bootstrap interval), D² (0.34) and the persistent component (0.47) were unchanged; within-tract noise ceilings and dispersion tests are reported for both versions."

---

## 3. Calibração do teste de dispersão (R8)

**Pergunta.** Rejeitar o Poisson em 4% dos setores, com α = 5%, indica excesso de variação?

**Método.**
- (i) **Nulo de Poisson puro:** 12 meses de Poisson na média mensal observada de cada setor com ≥ 1 evento e o mesmo teste (χ² com 11 g.l.), em 200 réplicas.
- (ii) **Nulo pelo pipeline:**
  - Eventos Poisson por setor × estrato × mês, com taxa constante em 2024–2025 igual à contagem reconciliada de 2025 do estrato.
  - Cada evento é geocodificado com a fração observada do **distrito × estrato** em 2025 (média de 0,83). A unidade é o estrato porque é nele que a reconciliação supõe ausência ao acaso; a fração por setor exigiria saber onde caíram os eventos sem coordenada, que é justamente o que não se observa.
  - Os não geocodificados são reconciliados como na produção (esperado e um sorteio) e o teste é aplicado a 2025. Também 200 réplicas.
- O conjunto de setores testados segue a mesma regra do observado: média maior que 0 e média de pelo menos 1 por mês.

| Versão | Observado: ≥ 1 evento / ≥ 1 evento/mês | Nulo calibrado: ≥ 1 evento / ≥ 1 evento/mês |
|---|---|---|
| Reconciliado (produção) | 3,9% / 14,2% | **pipeline: 1,7% [1,5–2,0] / 2,2% [1,6–2,9]**; Poisson puro: 3,6% [3,3–3,9] / 4,6% [3,7–5,6] |
| Imputado inteiro | 6,5% [6,3–6,7] / 17,7% [16,7–18,8] | pipeline: 3,5% [3,2–3,9] / 4,7% [3,9–5,4] |
| Só geocodificado | 6,8% / 19,4% | pipeline: 3,6% [3,3–4,0] / 4,7% [3,7–5,7]; Poisson puro: 3,7% / 4,6% |

**Implicação.** O teste é conservador em contagens baixas: o nulo de Poisson puro rejeita 3,6%, não 5%. Com contagens reconciliadas ele é ainda mais conservador, rejeitando 1,7%, porque a parte alocada varia menos que um Poisson.

Contra o nulo correto, o observado tem **excesso em todas as versões**: 2,3 vezes o nulo em todos os setores e 6,4 vezes nos setores com ≥ 1 evento por mês (14,2% contra 2,2%). "Only 4%" sugere ausência de variação, e a calibração mostra o contrário.

**Frase proposta (Results).** "A per-tract dispersion test rejected Poisson noise in 3.9% of tracts and in 14% of tracts with at least one event per month, against 1.7% and 2.2% expected under a null simulated through the same reconciliation; with integer imputations of the reconciled events, 6.5% and 18% (null 3.5% and 4.7%)."

**Methods (+60 palavras).** "Null rejection rates were simulated (200 replicates) by drawing Poisson events per tract, stratum and month at constant 2025 rates, geocoding each with the observed district–stratum share and reconciling the rest as in production."

---

## 4. Recuperação da reconciliação por ocultação (R4/R2)

**Pergunta.** Quando a coordenada é conhecida, a reconciliação recupera a contagem verdadeira? E quanto da suavização e da vantagem do histórico ela fabrica?

**Método.**
- Universo: os eventos de celular geocodificados de exploração, 2022–2025 (a verdade conhecida).
- Cada evento perde o setor, mas mantém distrito e estrato, com probabilidade igual à fração sem coordenada observada no estrato: residência 0,90, trilhos 0,81, outros 0,17, via pública 0,10, comércio 0,07, ônibus 0,004. No total, 12% dos eventos são ocultados.
- Três cenários:
  - `mar`: ao acaso dentro do estrato.
  - `mnar_crime`: logit com β = 1 por desvio-padrão do log da contagem anual do setor (oculta mais onde há mais crime).
  - `mnar_residencial`: β = 1 por desvio-padrão da parte residencial da testada.
- Nos cenários não aleatórios, o intercepto de cada estrato foi calibrado para manter a mesma fração média.
- Reconciliação de produção e comparação em 2023–2025 (2022 só como janela), com 10 réplicas por cenário.

| Medida (verdade = só geocodificados) | MAR | MNAR crime | MNAR residencial |
|---|---|---|---|
| r recuperada × verdadeira, anual / setor × mês | 0,999 / 0,993 | 0,973 / 0,966 | 0,998 / 0,992 |
| Variância mensal dentro do setor-ano, recuperada ÷ verdadeira (agregada) | **0,87** [0,87–0,88] | **0,65** [0,64–0,66] | 0,90 [0,90–0,91] |
| A mesma razão, mediana dos setores com ≥ 1/mês | 0,88 | 0,95 | 0,92 |
| Teto dentro do setor: verdadeiro 0,657 → recuperado | 0,607 | 0,470 | 0,619 |
| Rejeita Poisson em 2025 (verdadeiro 6,8% / 19,4% em ≥ 1/mês) | 3,7% / 14,6% | 4,8% / 14,3% | 3,4% / 15,2% |
| R² da média de 12 meses: verdade → verdade 0,652; recuperada → recuperada | 0,684 | 0,659 | 0,683 |
| R² dentro do setor, mesmo par: 0,054 → | 0,068 | 0,054 | 0,066 |
| Mesmo preditor (geocodificados restantes ÷ cobertura): R² contra recuperada / contra verdadeira | 0,682 / 0,648 | 0,656 / 0,613 | 0,680 / 0,648 |

**Implicação.**
- Sob ausência ao acaso dentro do estrato, a reconciliação recupera quase perfeitamente onde está o crime (r = 0,99 por setor-mês).
- Mas ela **suaviza o mês a mês**: tira 13% da variância dentro do setor, baixa o teto e corta à metade as rejeições.
- Ela também **fabrica vantagem para o histórico**: o mesmo preditor ganha 0,03 de R² total e 0,014–0,016 de R² dentro do setor (cerca de +26% a +30%) contra a contagem reconciliada.
- Se a ausência cresce com o crime do setor, a suavização chega a 35% e o teto dentro do setor cai de 0,66 para 0,47.
- Logo, o teto de 0,56 nos dados reconciliados é provavelmente uma **subestimativa** do teto verdadeiro.
- Limite do teste: o universo são os geocodificados, que já são uma seleção.

**Frase proposta (Methods ou ED).** "Hiding the coordinates of geocoded events at each stratum's observed missing rate and reconciling them recovered tract-month counts (r = 0.99) but removed 13% of within-tract monthly variance (35% when missingness rose with tract crime) and raised the R² of the 12-month historical mean from 0.65 to 0.68; the noise ceiling of reconciled counts is therefore conservative."

---

## 5. Repontuação do benchmark, só exploração (R2)

**Pergunta.** A paridade da média histórica com o ensemble na captura e o ganho de CRPS dependem da reconciliação?

**Método.**
- Previsões gravadas de 2025, com o ensemble reconstruído como em `select_run.load` e o φ de cada modelo de `resultados_benchmark_dev.json` (o do ensemble ajustado na validação).
- Alvos:
  - (i) y reconciliado, com três CRPS (produção ⌈y⌉, y real e y arredondado);
  - (ii) as 20 imputações inteiras (média dos escores);
  - (iii) y geocodificado, com cada μ multiplicado pela fração geocodificada as-of do setor nos 12 meses anteriores (média 0,77). O φ não muda com o afinamento binomial da NB2.
- Captura = média mensal do hit rate (`hotspot.monthly_average`) em 1% e 5% da área de exploração. Diferenças com bootstrap por distrito.

| Alvo | Habilidade de CRPS contra o GLM: média hist. / GNN / ensemble | Captura 5%: média hist. → ensemble (dif. ens − m.h.) | Captura 1%: m.h. → ens. |
|---|---|---|---|
| (i) reconciliado, CRPS da produção | −0,1% / 3,4% / 2,7% | 50,6% → 51,7% (+1,0 pp; 0,2 a 1,9) | 25,6% → 26,5% |
| (i) reconciliado, CRPS de y real | −1,7% / 3,8% / **6,0%** | igual ao anterior | igual |
| (i) reconciliado arredondado | −1,8% / 3,5% / 6,1% | 52,0% → 53,2% (+1,2 pp; 0,4 a 2,1) | 26,7% → 27,7% |
| (ii) imputado inteiro, média de 20 | −1,6% / 3,7% / 5,8% [5,7–5,9] | 50,6% → 51,7% | 25,6% → 26,5% |
| (iii) geocodificado, μ × fração as-of | −0,8% / 2,3% / 4,4% | 47,6% → 48,6% (+1,0 pp; 0,3 a 1,7) | 23,5% → 24,1% |

Com o CRPS correto, a diferença ensemble − média histórica é −0,019 (−0,027 a −0,012). No imputado é −0,018 e no geocodificado −0,011 (−0,015 a −0,009).

**Implicação.**
- **A paridade não depende da reconciliação.** Em todas as versões o ensemble captura cerca de 1 ponto percentual a mais que a média histórica, com o intervalo acima de zero.
- A captura esperada com imputações é igual à da produção, porque o total do mês é fixo.
- Isso era de esperar: a média histórica do benchmark usa geocodificados ÷ cobertura, não a série reconciliada.
- **O ganho de CRPS também persiste:** o ensemble fica de 4% a 6% abaixo do GLM e a média histórica fica abaixo do GLM.
- **O que muda o tamanho e o ranking é a definição do CRPS (destaque acima), não a reconciliação.**

**Frase proposta (Results).** "…the stacked ensemble improved the CRPS over a negative binomial GLM by 6% (difference −0.016, 95% interval −0.023 to −0.011) and the best single model by 5% (−0.012, −0.018 to −0.008), but added about one percentage point to the share of crime captured, also when scored against geocoded events only."

Os números desta frase são dos 96 distritos. Esse escopo exige refazer a Fig. 6d.

---

## 6. Onde mora a variação mensal (R1)

**Pergunta.** O teto dentro do setor de 0,56 é geral ou concentrado?

**Método.** Teto de ruído e R² do ensemble dentro do setor (2025) por terço da média mensal entre os 16.432 setores com ≥ 1 evento, no 1% do topo (213 setores, como em `dispersao`) e sem ele. "Excesso" é a parte do numerador do teto, Σ (SS − 11ȳ), que cai em cada grupo; nos terços baixos ela pode ser negativa.

| Grupo (média mensal) | Setores | Parte do crime | Teto dentro: produção / imputado / geocodificado | R² do ensemble dentro | Parte do excesso: produção / imputado |
|---|---|---|---|---|---|
| 1º terço (≤ 0,10) | 5.478 | 2,7% | 0 / 0 / 0 | 0,018 | −0,3% / 0,0% |
| 2º terço (0,10–0,34) | 5.477 | 10,7% | 0 / 0,03 / 0,05 | 0,023 | −0,7% / 0,3% |
| 3º terço (> 0,34) | 5.477 | 86,6% | 0,59 / 0,62 / 0,62 | 0,020 | 101% / 100% |
| 1% do topo (≥ 6,5) | 213 | 33,7% | **0,78** / 0,79 / 0,80 | 0,034 | **95%** / 90% |
| Sem o 1% do topo | 16.219 | 66,3% | **0,08** / 0,17 / 0,19 | 0,003 | 5% / 10% |
| Todos | 16.432 | 100% | 0,56 / 0,58 / 0,58 | 0,018 | 100% |

**Implicação.**
- O teto de 0,56 é quase todo do 1% de setores com mais crime: 90–95% do excesso, com teto de 0,78.
- Nos outros 99%, que têm dois terços do crime, o teto dentro do setor é de 0,08 a 0,19. Nos dois terços de menor contagem, o teto é zero: não há variação acima do Poisson a detectar.
- Os modelos falham inclusive onde ela existe: R² de 0,034 contra um teto de 0,78 no topo.
- A formulação correta separa os dois fatos. A detecção é limitada pela contagem (fora do topo, o teto é baixo). A previsão falha onde a variação é detectável. Nada disso mostra que a variação seja imprevisível: mostra que os modelos e as variáveis testados não a capturam.

**Frase proposta (Results, substitui "Within tracts, it explained…").** "Within tracts, it explained R² = 0.018 of a ceiling of 0.56 (0.58 with integer imputations). The ceiling comes almost entirely from the 1% of tracts with most crime, where it reaches 0.78 and the ensemble explains 0.03; in the other 99% it is 0.08–0.19. The ceiling assumes Poisson noise and bounds what any forecast could explain, not what the available covariates can."

---

## Quadro final: afirmações do manuscrito

| Afirmação | Veredito | Evidência (JSON) | Redação proposta |
|---|---|---|---|
| "too sparse to detect or forecast" (resumo, introdução, discussão) | **não sustentada** | Há excesso sobre o nulo calibrado (14% contra 2% em ≥ 1/mês). A variação está no topo (teto de 0,78), onde é detectável. O que falha são os modelos (R² de 0,03). | "Month-to-month variation within tracts exceeds Poisson noise mainly in the tracts with most crime, and the forecasting models we tested capture little of it." |
| "real month-to-month variation exists" | **sustentada**, com qualificação | O excesso de rejeição aparece em todas as versões e o teto é de 0,56–0,58. Mas está concentrada no 1% do topo. | Acrescentar "concentrated in the 1% of tracts with most crime". |
| "rejected Poisson in only 4%" | **não sustentada** como interpretação | O nulo para contagens reconciliadas é 1,7%: o observado é 2,3 vezes o nulo (6,4 vezes em ≥ 1/mês). | Frase da tarefa 3, sem "only". |
| "these shares are lower bounds" | **sustentada**, com qualificação | A reconciliação reduz as rejeições: imputado 6,5% contra 3,9%; na ocultação, 6,8% → 3,7%. Mas o só-geocodificado também é seletivo. | "Reconciliation lowers both the observed (3.9% against 6.5% with integer imputations) and the null rejection rate (1.7% against 3.5%)." |
| "the ensemble reached 87–99% of the ceiling at every scale" | **qualificada** | Vale para a variação entre + dentro (0,87 em setor × mês; 0,86 com imputações). Dentro do setor, é 3%. | "…87–99% of the between-and-within ceiling at every scale, but 3% of the within-tract ceiling at the tract-month scale." |
| "forecasts add little to a stable map of past crime" | **qualificada** | Robusta à reconciliação: +1 pp de captura em todas as versões. Mas, com o CRPS correto, o ensemble melhora 6% sobre o GLM e 7,5% sobre a média histórica (−0,019 de 0,248). | "Forecasts improved probabilistic scores by 5–6% over the best baseline but added about one percentage point to the share of crime captured." |
| "the persistent component (48%)" | **sustentada** | 46,5% [46,4–46,6] com imputações e 45,7% só geocodificado; defasagem 3 de 0,62. | Opcional: "(47% with integer imputations of reconciled events)". |

Mais uma afirmação afetada, fora da lista: "0.48 for the tract's historical mean" (Fig. 5a). É **qualificada**: o valor cai para 0,39 com imputações e 0,37 só geocodificado, porque a alocação esperada reproduz o histórico. "Where crime concentrates most, its history says more" continua valendo, com margem menor.

## Arquivos

- `src/cityomics/atlas/reconciliacao.py`: módulo novo, com `reconcile_draw`, `reparte`, `crps_nb_real`, `repontua_crps` e `run`.
- `tests/test_parecer_reconciliacao.py`: 18 testes.
- `data/processed/atlas/fenotipo/reconciliacao.json`: agregados; a fonte de todos os números acima.
- `data/processed/atlas/fenotipo/reconciliacao_imputacoes.parquet`: 20 imputações por setor × mês, só local.
