# F6 — Atlas mínimo do CityOmics (desenvolvimento, 2022–2025)

Specs: [spec-atlas.md](../spec-atlas.md) (emendado), [spec-figuras.md](../spec-figuras.md). Decisões D38–D62. Código em `src/cityomics/atlas/`, saídas em `data/processed/atlas/` (fora do git). Para regerar: `cityomics atlas run`.

**Duas salvaguardas:**
- Nada de 2026 é lido (`atlas/guard.pre2026`).
- Toda análise que usa crime exclui os 19 distritos do cofre espacial (`prereg/atlas_vault.json`, D53). Os números abaixo vêm dos 77 distritos de exploração (21.331 setores).

## 1. Genes do lote (`genes_lote.py`)

- **Células:** 1.651.813 lotes fiscais (a chave `sql_base`; ~17 mil chaves tinham polígonos repetidos e foram unificadas). 1,61 milhão têm IPTU 2025.
- **Testada:** mediana de 7,6 m. É a exposição de cada lote à rua (D51).
- **CNPJ:** snapshot de 2025-12 (D56). São 2,49 milhões de estabelecimentos ativos em SP.
  - **Ligação ao lote:** 73,8% pelo endereço do IPTU (CEP + número → SQL), ou 82% sem contar os MEI. Pelo ponto do CNEFE dentro do lote eram só 31,7%.
  - **MEI:** 957.599 vigentes, contados à parte (D60: nunca saem da máquina).
- **Genes:** 30 no total, sendo 18 do IPTU e 12 do CNPJ (11 grupos de CNAE + MEI).

## 2. Tipos de lote (`typing.py`)

- **Método:** PCA com 15 componentes (90% da variância).
- **Estabilidade sem crime (D53):** Leiden em 8 subamostras de 80 mil lotes por resolução, com rótulos transferidos a 40 mil lotes comuns e comparados por ARI. Alvo de 10 a 16 tipos:

  | Resolução | ARI médio | Tipos (mediana) |
  |---|---|---|
  | 0,02 | **0,973** | 14 |
  | 0,04 | 0,925 | 20 |
  | 0,07 | 0,909 | 23,5 |
  | 0,11 | 0,949 | 27,5 |
  | 0,16 | 0,792 | 31,5 |

- **Referência:** Leiden em r = 0,02 sobre 80 mil lotes estratificados por distrito.
  - 4 tipos minúsculos (< 0,3%) foram fundidos.
  - Transferência kNN para todos os lotes.
- **Sub-agrupamento vertical:** o tipo misto absorveu os prédios (81% dos lotes com ≥ 8 pavimentos). Um sub-agrupamento por regra de genes (≥ 4 pavimentos ou ≥ 8 unidades) separou 10.281 lotes como "vertical residencial e misto", o refinamento usual de um grupo heterogêneo.
- **Baseline:** o k-means no estilo OAC concorda com o Leiden em ARI = 0,71.
- **Os 12 tipos** (nomes por regras sobre o perfil médio, sem crime):

  | Tipo | Lotes |
  |---|---|
  | Residencial horizontal popular | 604.523 |
  | Residencial horizontal médio | 546.677 |
  | Terreno vago | 89.076 |
  | Misto residencial e comercial | 87.687 |
  | Comércio de rua popular | 62.974 |
  | Casa e comércio atacadista | 57.156 |
  | Residencial horizontal alto padrão | 46.626 |
  | Residencial de esquina | 41.890 |
  | Comércio de rua médio | 26.235 |
  | Serviços e equipamentos | 21.916 |
  | Indústria e galpões | 18.399 |
  | Vertical residencial e misto | 10.281 |

- **Favelas:** entram como 3.879 pseudo-células FCU (D54). A exposição é dada em domicílios informais × 7,0 m, a testada por unidade dos lotes populares. Nos mapas, a FCU prevalece sobre o cadastro: em favelas como Paraisópolis, os lotes fiscais aparecem como "terreno vago", porque as casas informais não pagam IPTU.

## 3. Arquitetura (`niches.py`)

- **Vizinhança:** grafo kNN (k = 8) com 13,2 milhões de arestas e 100 permutações restritas a distrito × decil de densidade (D59).
  - A atração mais forte entre tipos diferentes é entre os comércios: atacadista ↔ comércio popular (z = 99), comércio popular ↔ misto (z = 81), comércio médio ↔ popular (z = 78).
  - A maior segregação é entre terreno vago e residencial popular (z = −216).
  - A auto-vizinhança é alta em todos os tipos. Nos lotes de esquina (z = 927) é um efeito geométrico: as quatro esquinas de um cruzamento são vizinhas.
- **Domínios:** composição do setor suavizada no anel de contiguidade e agrupada por k-means. O k = 8 foi escolhido pela silhueta (0,162). Nomes pelos elementos mais enriquecidos:

  | Domínio | Elementos mais enriquecidos |
  |---|---|
  | N1 | vago + arteriais |
  | N2 | popular + vago |
  | N3 | favelas + vago |
  | N4 | vias locais + coletoras |
  | N5 | vertical + arteriais |
  | N6 | popular + esquinas |
  | N7 | comércio médio + alto padrão |
  | N8 | médio + indústria |

## 4. Atribuição do crime às classes de célula (`attribution.py`)

- **Modelo:** y_s ~ Poisson(Σ_k E_sk · λ_k), ajustado por EM, com bootstrap de 500 reamostras por distrito.
- **Celular em 2025:** 121.434 casos nos setores de exploração. A composição sozinha explica D² = 0,34.
- **Taxas por km de frente (lotes) ou de rua, por ano:**

  | Classe | Roubos/km/ano | IC 95% |
  |---|---|---|
  | Comércio de rua médio | 70,5 | 48–96 |
  | Vertical residencial e misto | 36,7 | 19–56 |
  | Comércio de rua popular | 29,8 | 20–44 |
  | Serviços e equipamentos | 26,0 | 17–35 |
  | Misto residencial e comercial | 13,6 | 8–21 |
  | Ruas arteriais | 4,6 | 2,8–6,8 |
  | Ruas coletoras | 2,4 | — |
  | Ruas locais | 1,4 | — |
  | Favelas | 0,5 | — |
  | Residencial horizontal | 0,01–0,14 | — |

  Estações de trilho: 87 roubos por estação por ano. Terminais de ônibus: 71.
- **Validação pontual (D29, D51):** 100.347 eventos geocodificados de 2025, fora do cofre.
  - Destino dos eventos: 4.944 ligados a estações (até 100 m) e 93.483 ligados ao segmento de rua mais próximo, repartidos entre os lotes lindeiros pela testada.
  - Resultado: Spearman entre a taxa atribuída e a observada = **0,93**.
- **Sankey (D47/D57):** λ_k depende de 4 grupos teóricos. A decomposição usa Shapley exato com referência no setor médio, e o efeito de distrito entra como nó "espacial".

## 5. Quanto do "onde" é tecido (`variance.py`)

- A variância entre setores responde por **84%** da variância do celular setor × mês (ICC de 2025, setores de exploração).
- R² fora da amostra (CV por distrito) da taxa de 2025 do setor:

  | Conjunto | R² |
  |---|---|
  | Tipos | 0,22 |
  | Mesmos genes sem tipagem (comparador de H3, D55) | 0,26 |
  | Tecido (tipos + domínios + ruas) | 0,25 |
  | Tecido + covariáveis do setor | 0,31 |
  | Média histórica 2022–2024 | **0,48** |

- **Leitura honesta:** o tecido explica cerca de um terço da geografia do crime sem memória de crime nenhuma, e a tipagem não acrescenta nada sobre os genes brutos. O resto do "onde" é a persistência do próprio lugar (média histórica). Isso afina a D35: o tecido define o mapa de oportunidades, e a história do lugar fixa onde ele de fato se realiza.

## 6. Benchmark por distrito × trimestre (`models/letal_run.py`, D41/D61)

| Desfecho | Melhor modelo (CRPS) | Contra o NB-GLM |
|---|---|---|
| Letal | NB-GLM 1,076 | nenhum modelo melhor (LightGBM 1,120; Hawkes 1,093; BYM-EB 1,085) |
| Celular (pareado) | LightGBM 37,6 | −0,83, com p ajustado de 1,0 (não significativo) |

Na escala do órgão (distrito), os métodos não se separam.

## 7. A completar

- Destino (§3.5 emendado).
- Comunicação (multiverso, ED2).
- Confirmação no cofre: só depois da A11 (`prereg/A11_DRAFT.md`).
