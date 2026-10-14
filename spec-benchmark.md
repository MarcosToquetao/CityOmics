# Spec — Benchmark preditivo (Etapa 1 / Artigo de data science)

> Parte de [spec-overview.md](spec-overview.md). Depende de [spec-dados.md](spec-dados.md).

**Em resumo:** um torneio pré-registrado de métodos vindos de outras ciências contra baselines fortes, para prever celular (setor × mês) e violência letal (distrito × trimestre) em 2026. O Laya, ajustado e calibrado, entra como camada de decisão sobre essas representações. Cada família é avaliada por ablação.

## 1. Tarefas de previsão

| Tarefa | Unidade | Alvo | Saídas |
|---|---|---|---|
| T1 Celular | Setor 2022 × mês | Contagem reconciliada (D16/D27) | Distribuição de contagem (NB) + P(≥1) + P(≥k), com k = P90 do treino |
| T2 Violência letal | Distrito × trimestre | Contagem do composto (D20); CVLI estrito como sensibilidade | Distribuição de contagem + P(≥1) |

- **Horizontes (D25):** h=1 como primário; h=3 e h=6 como secundários.
- **Protocolo (D25):** os parâmetros ficam congelados com os dados até dez/2025. A cada mês m de 2026, as entradas (lags e features) são atualizadas com os dados disponíveis antes de m (regra as-of). Nenhum modelo é reajustado durante 2026.

## 2. Divisão temporal

```
2022 ────────── 2024 │ 2025 │ jan–set 2026 │ nov/26–mar/27
   treino            │ tuning│ validação    │ confirmação prospectiva
                     │ (origem móvel)
treino final = 2022–2025 → congelado → previsão de 2026
```

- **Tuning:** em 2025, com origem móvel e janela expansível. Para modelos com hiperparâmetros espaciais, CV bloqueada no espaço (blocos do tamanho do alcance da autocorrelação; Roberts et al. 2017).
- **Ajustado só no treino:** escalas, PCA, clusters e tipos (vindos do atlas), larguras de banda de KDE, embeddings e seleção de covariáveis (D12).
- **T2 usa histórico estendido** com SPSafe e CEM (D15), harmonizado por distrito ou DP.

## 3. Modelos

### 3.1 Baselines (obrigatórios)

Persistência (t−1), sazonal (mesmo mês do ano anterior), média histórica, space-time KDE, hotspot prospectivo, NB-GLM com lags.

### 3.2 Famílias de outras áreas

| Família (origem) | Implementação | Observação |
|---|---|---|
| ETAS / Hawkes com covariáveis (sismologia) | R `ETAS`/`stpphawkes` ou Python `BSTPP`; janela de disparo truncada (~1 km, ~60 dias) | Ajuste nos pontos geocodificados; integrado por setor |
| BYM2 / Knorr-Held espaço-temporal (epidemiologia) | R-INLA | Principal família para T2 |
| Near-repeat / Knox (epidemiologia) | `surveillance::knox` | Entra como features |
| MaxEnt com background do grupo-alvo (ecologia) | `elapid` / `maxnet` | Sem aplicação a crime encontrada na literatura |
| Risk Terrain Modeling (criminologia) | Camadas de POIs | Referência |
| LGCP / processo gaussiano (física e estatística) | `inlabru` SPDE | |
| Ripley K / two-point (astronomia) | `spatstat`, TreeCorr | Escolha de escalas e features |
| Painel espacial, GWR/MGWR (econometria) | PySAL `spreg`, `mgwr` | |
| LightGBM com lags espaciais e temporais (ML) | Perda Poisson/Tweedie | Recebe as features completas **e** o estado comprimido do Laya (D24) |
| Chronos / TimesFM zero-shot (foundation models) | Colab | Sem aplicação a crime encontrada |
| GNN espaço-temporal (STGCN ou similar) | PyG Temporal, no Colab | Grafo de adjacência entre setores |
| Ensemble empilhado | Pesos ajustados em 2025 | |

### 3.3 Laya (camada de decisão) — D2, D24, D30

- **Modelo:** `laya-typed-decisions` (ModernBERT-large, 421M, contexto de 1024), com pesos fixados por hash.
- **Braços:**
  1. **Laya FT (principal):** fine-tuning completo com RLCD em 2022–2024, recalibração isotônica em 2025.
  2. **Laya ZS (referência):** zero-shot + recalibração isotônica em 2025.
- **Perguntas:** `noul` para P(≥1) e P(≥k); `score` para a faixa de contagem (0, 1, 2–3, 4–7, 8+).
- **Estado serializado** (`laya/serialize.py`): em inglês, ≤1024 tokens, ID anônimo. Contém:
  - tipo/domínio do setor (do atlas);
  - top-10 genes marcadores (z-scores);
  - composição do nicho;
  - tendência do crime (3/6/12 meses);
  - escores de Hawkes, BYM2, KDE e MaxEnt;
  - calendário.
- **Ablações:**
  - com nomes reais (distrito/bairro), para medir o efeito do conhecimento prévio do modelo;
  - sem histórico de crime (D6);
  - sem cada bloco de escores de outras áreas.
- **Infraestrutura:** fine-tuning e inferência no Colab. Sobem só tabelas de estados anonimizados (D30). Todas as respostas ficam em cache (Parquet com hash do estado).

### 3.4 Seleção de covariáveis (D12)

- **Modelo teórico (núcleo pré-registrado):**
  - atividade rotineira: fluxo do Metrô, CNPJ de comércio e bares, POIs;
  - desorganização social: IPVS, renda, Δ do Censo;
  - CPTED: iluminação do entorno, VIIRS, calçadas;
  - mercado imobiliário: ITBI.
- **Modelo guiado por dados:** SHAP e permutação em LightGBM, mais stability selection, usando só 2022–2025 e CV bloqueada.
- A comparação entre os dois modelos em 2026 é um resultado do artigo.

## 4. Avaliação (F7)

| Grupo | Métricas |
|---|---|
| Hotspot operacional | Curvas de hit rate, PAI e PEI (e PEI* se a fórmula for confirmada) em 0,5/1/2/5/10% da área; dispersão e complementaridade (Adepeju et al. 2016) |
| Probabilístico | Log score, CRPS da NB (`scoringRules::crps_nbinom`), Brier para P(≥1) com decomposição; scores calculados também só nas células com contagem diferente de zero |
| Calibração | PIT randomizado, reliability diagrams, ECE (global e por grupo de renda/raça), `surveillance::calibrationTest` |
| Significância | Diebold–Mariano com block bootstrap (meses × blocos espaciais), correção para comparações múltiplas |
| Estabilidade | Desempenho mês a mês em 2026; quebra de cobertura em abr/2026 |
| Equidade (D11) | Hit rate, calibração e área sinalizada por quintil de renda e por composição racial do setor |

- **Análise de poder (T2):** pré-registrada, com tamanho mínimo de efeito detectável dado o número de células de distrito × trimestre.
- **Hipótese-ponte (com spec-atlas):** acrescentar as features de omics (tipos, nichos, domínios, contexto MISTy, velocity urbana) ao melhor modelo de §3. O ganho é testado em 2026 com Diebold–Mariano.

## 5. Pré-registro (F4)

Registrado no OSF **até 31/out/2026** (depende só das specs; D32), antes de ler `sealed_2026/` para avaliação. Emendas datadas são permitidas até essa leitura. Conteúdo:
- desfechos, unidades, horizontes e protocolo;
- lista de modelos e de ablações;
- métricas primárias (PAI a 1% e 5%, CRPS, Brier) e secundárias;
- núcleo teórico de covariáveis;
- hipótese-ponte;
- análise de poder;
- **declaração de exposição prévia** a 2026 (site público do MapaSegurancaSP);
- janela prospectiva como confirmação.

## 6. Artefatos do artigo

- Tabela principal: modelo × métrica × desfecho × horizonte, com intervalos por bootstrap.
- Figuras: curvas de PAI, reliability, desempenho mês a mês, ablações (quanto cada família agrega), auditoria de equidade.
- Repositório reprodutível: `cityomics run --until 2025` reproduz a tabela de tuning; o snapshot dos dados agregados vai para o Zenodo.

## Decisions Log

| ID | Topic | Decision | Rationale | Source | Date |
|---|---|---|---|---|---|
| D3 | Papel do modelo de decisão | Camada final + baselines | Afirmação defensável | Interview | 2026-10-14 |
| D6 | Histórico de crime | 2ª modalidade com ablação | Circularidade | Interview | 2026-10-14 |
| D10 | Validação | 2026 lacrado; pré-registro; janela prospectiva | Blindagem | Interview | 2026-10-14 |
| D11 | Ética | Auditoria de equidade; enquadramento preventivo | Loops de feedback | Interview | 2026-10-14 |
| D12 | Seleção | Teórica + guiada por dados só até 2025 | Não contaminar o teste | Interview | 2026-10-14 |
| D20 | Violência letal | Composto primário | Poder estatístico | Red Team | 2026-10-14 |
| D24 | Laya | FT principal, ZS como referência, IDs anônimos, LightGBM com o mesmo estado | Reprodutível e justo | Red Team | 2026-10-14 |
| D25 | Protocolo | Parâmetros congelados, entradas atualizadas, h=1/3/6 | Quebra de nível sem vazamento | Red Team | 2026-10-14 |
| D26 | Teste primário | 2026 = validação; janela prospectiva = confirmação | Exposição prévia | Red Team | 2026-10-14 |
| D30 | Colab | Laya, Chronos e GNN no Colab; só dados anônimos | GPU local de 4 GB | Red Team | 2026-10-14 |

## Dependency Graph & Implementation Order

```
features (lags as-of, KDE, near-repeat, Hawkes, MaxEnt) ─► baselines ─► famílias de outras áreas ─► LightGBM
                                                                              │
                     atlas (tipos/nichos ajustados até 2025) ─► laya/serialize ─► Laya ZS ─► Laya FT ─► ensemble
                                                                              │
eval/* (implementado e testado com 2025) ─► pré-registro ─► abertura de 2026 ─► janela prospectiva
```

1. `eval/` primeiro, testado com 2025 (métricas, PIT, DM, equidade).
2. Features e baselines.
3. Famílias de outras áreas (R-INLA em paralelo com Python).
4. Serialização e Laya ZS/FT no Colab.
5. Ensemble → congelamento → pré-registro → avaliação.
