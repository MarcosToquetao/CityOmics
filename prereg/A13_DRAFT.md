# A13: modelos congelados, Laya e H4 — vigente: datada em 2026-10-27 com H4 exploratório (opção a)

> Rascunho de 2026-10-27, preparado sob delegação. **Não vale até o autor revisar, datar e copiar a linha final para `AMENDMENTS.md`, antes do FREEZE-A.** Nada de 2026 foi lido. O código está em `src/cityomics/models/congelar.py` (`cityomics freeze models`); o resumo dos arquivos fica em `data/models/frozen/MANIFESTO.json`.

## 1. Modelos de crime (H1)

As janelas são as do desenvolvimento deslocadas um ano, como `benchmark_run` previa:

| Etapa | Ajuste | Previsão | Para quê |
|---|---|---|---|
| Pesos do ensemble | 2023-01..2025-06 | 2025-07..2025-12 | Pesos por deviance de Poisson e φ do ensemble, fora da amostra |
| Modelos finais | 2023-01..2025-12 | 2026 (depois de aberto o cofre) | Os 14 modelos, cada um com o φ (NB2) do próprio período de ajuste |

- Os 14 modelos são gravados em `data/models/frozen/crime/<modelo>.joblib`, e os pesos do ensemble em `ensemble.json`. Os sha256 desses arquivos entram no manifesto.
- Em 2026 só os lags mudam, mês a mês, pela regra as-of (D25). `congelar.prever()` aplica os modelos congelados à tabela de 2026.
- O código de ajuste é o mesmo do benchmark (`zoo.fit`). Ele reproduz exatamente as previsões gravadas de 2025: a diferença máxima é zero no GLM, na média histórica, no KDE e no LightGBM núcleo.

## 2. Laya (H2) — correção do protocolo registrado

O §5.1 diz "fine-tuned with RLCD on 2022–2024 and isotonic-recalibrated on 2025". O que foi feito difere em dois pontos, e o texto do registro deve ser corrigido para refletir isso:

- **Dados do ajuste:** só 2024-H1, com 60 mil estados de 25% dos setores (`docs/F5_laya.md`), não 2022–2024.
- **Perda:** soft cross-entropy, sem o termo de política do RLCD. O RLCD padrão divergiu, e a troca está documentada em `docs/F5_laya.md`.

O braço congelado fica assim:

- **Laya-FT:** o checkpoint do ajuste acima, identificado pelo sha256 de cada arquivo da pasta no Drive. O hash é calculado por `notebooks/colab/laya_hash_pesos.ipynb` e gravado em `data/models/frozen/laya_ft/pesos_sha256.json`. A esse checkpoint se soma a recalibração isotônica ajustada nas 81.900 previsões de 2025 (`recalibrador_isotonico_2025.joblib`).
- **Comparador do H2 (`lgbm_estado`):** LightGBM binário no mesmo estado comprimido e no mesmo treino (2024-H1), com os parâmetros de `laya.evaluate.lgbm_on_state` e a mesma recalibração isotônica de 2025.
- **Laya-ZS:** continua só como referência, sem arquivo congelado. Os pesos são os públicos da base.

## 3. Destino (H4) — decisão do autor

O H4 compara Laya-FT e Markov de tipo × nicho nas transições 2025-S2 → 2026-S1. Com as decisões D42 e D56:

- as transições ficaram **anuais**, só com o IPTU (2012–2025, 2021 mascarado);
- o destino com Laya foi para o suplemento e **nunca rodou**.

O que foi congelado:

- **Markov de família × domínio do tecido** (`data/models/frozen/destino/markov_familia_dominio.parquet`);
- as transições anuais de 2012 a 2025, por domínio do setor do lote, com suavização de Laplace (α = 1);
- as famílias do IPTU vêm do classificador de `atlas/fate.py`.

**Escolha do autor (marque uma):**
- [x] **(a) Escolhida pelo autor (2026-10-27):** o H4 sai da família confirmatória e vira descrição exploratória. O Markov congelado prevê a família de 2026 a partir da de 2025, e reportamos a log-loss sem teste contra o Laya.
- [ ] (b) Manter o H4. É preciso rodar o destino com Laya no Colab antes do FREEZE-A, com as transições anuais 2012–2024 para ajuste e 2024→2025 para recalibração.

## 4. Seleção e congelamento em duas etapas

- **`selection.json` completo**, a aplicar junto com a A12. As quatro primeiras chaves são as da A12; as três novas são deste documento:
  - `best_baseline_crps`: `glm`;
  - `best_baseline_pai1`: `media_historica`;
  - `best_crossdomain_crps`: `ensemble`;
  - `best_crossdomain_pai1`: `ensemble`;
  - `laya_ft`: `laya_ft`;
  - `lightgbm_compressed_state`: `lgbm_estado`;
  - `markov_fate_baseline`: `markov_familia_dominio`.
- **O `freeze.py` passa a ter as duas etapas da A11:**
  - **FREEZE-A:** exige A12 e A13 datadas e o hash do Laya. Grava `FREEZE_A_MANIFEST.json`, sem chave.
  - **FREEZE-B:** exige a A11 datada, a confirmação do atlas feita e os hashes do FREEZE-A inalterados. Grava `FREEZE_MANIFEST.json` e `UNSEAL_KEY`.

## Linha para `AMENDMENTS.md`

| 2026-10-XX | 4.2, 5.1, 5.2, H4 | A13. Modelos congelados: os 14 modelos de crime reajustados em 2023-01..2025-12, pesos do ensemble e φ em 2025-07..2025-12 fora da amostra; Laya-FT = checkpoint por sha256 (ajuste em 2024-H1 com soft cross-entropy, não RLCD em 2022–2024) + isotônica de 2025; comparador do H2 = LightGBM no mesmo estado e treino + isotônica de 2025; Markov de família × domínio (transições anuais do IPTU 2012–2025) como linha de base do destino; H4 [(a) passa a exploratório / (b) mantido]; congelamento em duas etapas (A e B) | Fixar os arquivos e as identidades antes de abrir 2026 e registrar o protocolo do Laya como de fato foi executado |

## Hash dos pesos do Laya-FT (2026-10-27)

sha256 do `model.safetensors` (842.609.220 bytes), idêntico na pasta final e em `checkpoint_latest`: `4c56e1cd05721c152344451c1807d03a3936639b1c2fb8e4e40d19e8b0551fa0`. Os hashes de todos os arquivos da pasta estão em `data/models/frozen/laya_ft/pesos_sha256.json`. O `tokenizer_config.json` difere entre a pasta final e `checkpoint_latest` (o primeiro foi ajustado na inferência por `_fix_tokenizer_config`); vale o da pasta final.
