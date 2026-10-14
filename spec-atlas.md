# Spec — Atlas CityOmics (Etapa 2 / Artigo de ciências urbanas)

> Parte de [spec-overview.md](spec-overview.md). Depende de [spec-dados.md](spec-dados.md). Alimenta a hipótese-ponte de [spec-benchmark.md](spec-benchmark.md).

**Em resumo:** São Paulo lida como um tecido. Os lotes são células, tipadas só por covariáveis nativas. Os setores são spots de composição conhecida, o que permite estimar quanto cada tipo de lote contribui para o crime do setor. Nichos e domínios descrevem a arquitetura do tecido. A transição semestral de tipo dos lotes funciona como "destino celular", previsto pelo Laya. Cada método de omics é comparado com seu análogo urbano clássico.

## 1. Mapeamento conceitual

| Transcriptômica espacial | CityOmics |
|---|---|
| Célula segmentada (Xenium/MERFISH) | Lote fiscal (+ favela como pseudo-lote FCU) |
| Spot (Visium) | Setor censitário 2022 |
| Região anatômica | Distrito |
| Genes (contagens) | Atributos nativos do lote: IPTU, ITBI, CNPJ/CNAE, CNEFE (D22) |
| Proteínas / 2ª modalidade | Crime (desfecho; nunca define o tipo, D6) |
| Library size / fatores de tamanho | Área, população, unidades do lote |
| Tipo celular | Tipo de lote (Leiden), ajustado só até 2025 |
| Nicho / vizinhança | Composição de tipos no entorno (anéis em k-vizinhos / distância) |
| Destino celular / lineage tracing | Transição semestral do tipo de lote, 2012–2026 (D23, D31) |
| Lotes / batches | Semestres e anos |

**Novidade:** nenhum trabalho publicado aplica esse conjunto de ferramentas a cidades. O único antecedente informal é um post de blog. O risco é a crítica de que seria geodemografia com nomes novos. **Por isso, cada módulo tem um baseline urbano** e o artigo reporta também onde a omics não acrescenta nada.

**Literatura a enfrentar:**
- Zormpas et al. 2023 (*Cell*): conceitos da geografia aplicados à omics.
- Fleischmann & Arribas-Bel 2022: assinaturas espaciais.
- OAC e a tipologia urbanodemográfica de SP (*Estudos Avançados* 2019).
- Yuan, Zheng & Xie 2012 (DRoF).
- Delmelle 2016 (trajetórias de bairros).

## 2. Objetos de dados

- `MuData` com duas modalidades:
  - `lote` (~1,5 milhão × genes nativos; o número de lotes ainda será verificado);
  - `setor` (~27 mil × genes do setor + composição de tipos + crime como `.obsm`).
- Coordenadas em `.obsm['spatial']` (EPSG:31983).
- Grafos espaciais via `squidpy.gr.spatial_neighbors`: Delaunay para setores, kNN/raio para lotes.
- Um objeto por semestre de 2012-S1 a 2026-S1. Os tipos são ajustados até 2025-S2 e **projetados** em 2026.

## 3. Módulos principais (corpo do artigo) — D17

### 3.1 Tipagem de lotes
- **Pré-processamento:** log1p e resíduos de Pearson; HVG; PCA; kNN; Leiden; scVI no Colab, como alternativa.
- **Baseline:** k-means no estilo OAC sobre as mesmas variáveis padronizadas.
- **Métricas:**
  - estabilidade entre semestres (ARI de t para t+1);
  - interpretabilidade (genes marcadores por tipo);
  - poder de estratificar o crime (*sem* usá-lo na definição dos tipos).

### 3.2 Atribuição por tipo (composição conhecida) — D21, D29
- **Modelo:** `crime_setor,t ~ Poisson( Σ_k n_setor,k · λ_k,t · exp(u_setor) )`. Aqui n é o número de lotes de cada tipo, que é conhecido. λ é a taxa específica do tipo e u é o efeito espacial (BYM2 no INLA ou NumPyro).
- A versão para perfis censitários segue a mesma lógica, estimando o perfil específico de cada tipo de lote, no estilo TCA/CIBERSORTx.
- **Validação pontual (D29):** para os crimes geocodificados, ligar cada ponto ao lote mais próximo e comparar a taxa por tipo observada com a λ estimada. Isso responde à crítica de falácia ecológica.
- **Baseline:** regressão de composição sem efeito espacial e regressão por setor sem tipos.
- **Pergunta científica:** "risky facilities" (o lote) versus efeito de vizinhança.

### 3.3 Nichos e domínios
- **Nichos:** `squidpy.gr.nhood_enrichment` e `co_occurrence`, e vizinhanças celulares (Schürch et al. 2020).
- **Domínios:** CellCharter (multi-amostra) e Banksy (λ ajusta a ponderação entre tipo e domínio).
- **Baselines:** colocation quotient (Leslie & Kronenfeld 2011), regionalização SKATER/REDCAP/max-p, assinaturas espaciais.
- **Nulos:** permutações condicionadas à densidade populacional.

### 3.4 Genes espacialmente variáveis
- **Métodos:** nnSVG e SPARK-X sobre genes do lote e do setor; módulos com Hotspot.
- **Baseline:** Moran's I global e local (deixar claro que ele vem da geografia).
- **Saída:** quais atributos urbanos têm estrutura espacial além da densidade, e quais módulos coexpressos existem.

### 3.5 Destino celular — D4, D23, D31
- **Estado do lote no semestre s:**
  - estoques: CNPJ ativos por CNAE, preço/m² do último ITBI carregado adiante, tempo desde a última transação, SP156 no entorno;
  - **IPTU do ano anterior** como contexto defasado.
- **Transição:** `tipo(s) → tipo(s+1)`, separada em duas famílias:
  - **atividade:** mudanças por CNPJ, ITBI ou SP156, possíveis em qualquer semestre;
  - **cadastro:** mudanças por IPTU, só na virada do ano.
- **Janela:** treino de 2012-S1 a 2025-S2 (~27 transições); teste em 2025-S2 → 2026-S1. Alvarás entram como contexto a partir de 2020.
- **Modelos:**
  - Markov por tipo, e por tipo × nicho;
  - CellRank (kernel de transição observado + probabilidades de destino);
  - LightGBM multiclasse;
  - **Laya FT** (`choice` com K tipos; K ≤ ~20, porque o desempenho cai acima disso) e Laya ZS.
- **Métricas:**
  - P(muda): Brier e AUC;
  - entre os que mudam: macro-F1 e log-loss;
  - calibração;
  - tudo separado pelas duas famílias.
- **Amostragem:** a população inteira para os baselines. Para o Laya, todos os lotes que mudam mais uma amostra de igual tamanho dos que não mudam, com pesos de reamostragem. A inferência roda no Colab, com estados anônimos.
- **Desfecho criminal condicional:** P(crime no setor) segundo a trajetória dos tipos que o compõem. É a ligação com o benchmark.

## 4. Módulos suplementares — D17

| Módulo | Método | Baseline | Observação |
|---|---|---|---|
| Comunicação célula-célula | COMMOT / LIANA+ com fluxos da OD 2017 (zonas → lotes por pesos dasimétricos) | Modelo gravitacional (Wilson) | "Ligante" = o que o lugar emite (empregos, vida noturna); "receptor" = o que ele recebe |
| MISTy | Visões intrínseca / justaposta / paraview | Lag espacial simples | Quanto do crime vem do setor e quanto do entorno |
| Predição por imagem | Encoder congelado (DINOv2-small/ResNet) sobre ortofotos do GeoSampa, no Colab → regressão do perfil do setor | Najjar et al. 2018 | Análogo de ST-Net/iStar |

Os módulos suplementares só vão para o corpo do artigo se o resultado for forte.

## 5. Hipótese-ponte (com o benchmark)

As features de omics ajustadas até 2025 (tipo/domínio, composição do nicho, contexto MISTy, "velocity urbana" = vetor de mudança semestral) são acrescentadas ao melhor modelo do benchmark. O teste em 2026 é pré-registrado. Também testamos se os tipos são mais estáveis no tempo (ARI) do que o k-means.

## 6. Robustez

- **Sensibilidade à unidade:** comparar com H3 res 9 apenas como análise de MAUP, não como unidade principal.
- **Nulos:** permutações controlando população e densidade.
- **CV bloqueada:** no espaço e no tempo.
- **Resolução da tipagem:** estabilidade dos tipos de acordo com o parâmetro de resolução do Leiden.

## 7. Artefatos do artigo

- **Figura 1:** a cidade como tecido (UMAP dos tipos de lote + mapa).
- **Figura 2:** atribuição de crime por tipo, com validação pontual.
- **Figura 3:** nichos e domínios comparados aos baselines.
- **Figura 4:** destino celular, com fluxos de transição (PAGA/CellRank) e desempenho do Laya.
- **Recurso aberto:** objeto `MuData` agregado de SP (sem microdados) + código.

## Decisions Log

| ID | Topic | Decision | Rationale | Source | Date |
|---|---|---|---|---|---|
| D4 | Próximo passo | Desfecho + transição de tipo | Destino celular | Interview | 2026-10-14 |
| D6 | Genes vs desfecho | Tipos definidos sem crime | Circularidade | Interview | 2026-10-14 |
| D8 | Publicações | Atlas = artigo de ciências urbanas | Contribuições distintas | Interview | 2026-10-14 |
| D13 | Unidades | Lote → setor → distrito | Unidades orgânicas | Interview | 2026-10-14 |
| D17 | Escopo | 5 módulos principais + 3 suplementares | Foco | Interview | 2026-10-14 |
| D21 | Atribuição | Composição conhecida → taxas por tipo | Deconvolução seria um erro | Red Team | 2026-10-14 |
| D22 | Genes por escala | Lote nativo; setor com Censo etc. | Tipos significativos | Red Team | 2026-10-14 |
| D23 | Destino | Semestral; estoques + IPTU defasado; atividade vs cadastro | Evita trivialidade e artefato | Red Team | 2026-10-14 |
| D29 | Validação pontual | Pontos → lote → comparação com λ | Falácia ecológica | Red Team | 2026-10-14 |
| D31 | Janela | 2012-S1 → 2025-S2 treino; 2026-S1 teste | Genes consistentes | Red Team | 2026-10-14 |

## Dependency Graph & Implementation Order

```
units/lotes + covariáveis do lote ─► build_adata (por semestre) ─► typing ─┬─► attribution (+ validação pontual)
                                                                          ├─► niches / domains
                                                                          ├─► svg
                                                                          └─► fate (Markov → CellRank → LightGBM → Laya ZS/FT)
                                                       suplementares: misty · commot · image (depois do núcleo)
typing/niches/fate (até 2025) ─► features de omics ─► hipótese-ponte (spec-benchmark F7)
```

1. `build_adata` + `typing` (bloqueiam o resto).
2. `attribution`, `niches`, `svg` em paralelo.
3. `fate` (depende da tipagem semestral estável).
4. Suplementares.
