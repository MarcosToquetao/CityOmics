# CityOmics — Spec mestre

> Especificação gerada por `/interview-me` + red-team `/grilling` em 2026-10-14.
> Sub-specs: [spec-dados.md](spec-dados.md) · [spec-benchmark.md](spec-benchmark.md) · [spec-atlas.md](spec-atlas.md)

## Em resumo

| | |
|---|---|
| **Pergunta** | Métodos de outras ciências preveem melhor onde e quando o crime acontece em São Paulo? A cidade pode ser lida como um tecido, com o vocabulário da transcriptômica espacial? |
| **Desfechos** | Roubo/furto de celular (setor censitário × mês) · Violência letal composta (distrito × trimestre) |
| **Dados-base** | Microdados de BO da SSP-SP 2022–2026 (~470 mil registros/ano na capital) + covariáveis urbanas T1+T2 (~150–300 "genes") |
| **Unidades** | Lote fiscal (célula) → setor censitário 2022 (spot) → distrito (órgão) |
| **Modelo de decisão** | Laya (`laya-typed-decisions`, encoder de 421M) com fine-tuning e recalibração |
| **Validação** | Treino até 2025, validação em jan–set/2026, confirmação prospectiva em nov/2026–mar/2027 |
| **Produtos** | Artigo 1 (data science): benchmark preditivo · Artigo 2 (ciências urbanas): atlas CityOmics |

## Problema

Os modelos de predição de crime em SP usam poucas famílias de métodos e quase não testam a transferência de técnicas maduras de outras áreas. Exemplos dessas técnicas: processos auto-excitáveis da sismologia, mapeamento bayesiano de doenças da epidemiologia, modelos de distribuição de espécies da ecologia e correlação de dois pontos da astronomia. A transcriptômica espacial, por sua vez, desenvolveu um conjunto integrado de ferramentas: tipagem celular, nichos, domínios, genes espacialmente variáveis, atribuição por tipo e destino celular. Não encontramos nenhuma aplicação desse conjunto a cidades.

## Objetivos

1. Comparar, num benchmark pré-registrado, famílias de métodos de outras áreas com baselines fortes (persistência, KDE, NB-GLM) na previsão de 2026.
2. Usar o Laya como camada de decisão calibrada sobre representações vindas dessas áreas e medir o ganho por ablação.
3. Construir o atlas CityOmics de SP, com tipos de lote, nichos, domínios, atribuição de crime por tipo e trajetórias semestrais. Cada método de omics será comparado ao seu análogo urbano clássico.
4. Testar a **hipótese-ponte**: representações de omics, ajustadas só até 2025, melhoram a previsão de 2026 em relação ao melhor modelo do benchmark e são mais estáveis no tempo do que a geodemografia por k-means.

## Fora do escopo

- Ferramenta operacional de patrulha ou despacho policial (D11).
- Previsões no nível do indivíduo.
- Crimes que dependem da iniciativa policial (tráfico, porte de arma), porque medem a atuação da polícia e não a ocorrência.
- Base de violência doméstica (D14).
- Jev e outras APIs hospedadas de modelos (D24).
- Integração com uma segunda cidade (fica para trabalho futuro).

## Visão do sistema

```
SSP xlsx (2022–26) ─┐                     ┌─► Benchmark (Etapa 1) ─► Artigo 1
SPSafe / CEM ───────┼─► ingestão ─► unidades/reconciliação ─► covariáveis as-of ─┤
IBGE/GeoSampa/... ──┘    (snapshot)     (lote→setor→distrito)                    └─► Atlas (Etapa 2) ──► Artigo 2
                                                                    Laya (Colab) ◄──┴──► hipótese-ponte
```

- **Execução local** (12 núcleos, 30 GB de RAM): ingestão, unidades, covariáveis, modelos estatísticos, LightGBM e R-INLA.
- **Google Colab** (GPU): fine-tuning e inferência do Laya, scVI, encoders de imagem, Chronos/TimesFM e GNN. Só sobem dados agregados e anonimizados (D30).

## Ética e privacidade

- **Enquadramento:** prevenção, planejamento urbano e serviços às vítimas. Nada de despacho de patrulha.
- **Auditoria de equidade:** hit rate, calibração e área sinalizada, analisados por renda e raça do Censo 2022.
- **Desfechos:** só crimes reportados pela vítima, o que reduz o viés de feedback do policiamento.
- **Dados de BO:** número do BO, logradouro e coordenadas ficam só em `data/raw` local. Saídas públicas são agregadas, e a violência letal é publicada como taxa suavizada (posterior do BYM2).
- **Retenção:** os microdados brutos ficam guardados até a publicação mais 5 anos e depois são apagados. Os agregados são publicados.
- **Segredos:** ficam só em `.env` fora do git. Hoje não há nenhum em uso (D28).

## Riscos principais

| Risco | Mitigação |
|---|---|
| Crítica de "geodemografia com outro nome" | Cada método de omics é comparado com o análogo urbano (spec-atlas) |
| Persistência difícil de vencer | Baselines obrigatórios; o artigo reporta honestamente onde nada vence |
| 2026 já foi visto (o site publica esses dados) | Exposição declarada no pré-registro + janela prospectiva (D26) |
| Mudança de geocodificação em abr/2026 | Reconciliação hierárquica estratificada (D16/D27) |
| Violência letal esparsa | Desfecho composto + escala de distrito × trimestre + análise de poder (D20) |
| Queda real de roubos em 2026 (−14% a −34%) | Parâmetros congelados com entradas atualizadas (D25); desempenho reportado mês a mês |
| Portais públicos mudam ou saem do ar | Snapshot congelado com sha256 (D18) |

## Cronograma

| Período | Marco |
|---|---|
| out–nov/2026 | F0–F3: specs, ingestão, unidades e covariáveis |
| antes de abrir 2026 | F4: commit de congelamento (hashes dos modelos, melhores da classe) = chave do cofre; registro no OSF só na etapa final (D33) |
| nov/2026–fev/2027 | F5 benchmark (até 2025) e F6 atlas em paralelo |
| ~mar/2027 | Avaliação 2026 → submissão do Artigo 2 (atlas) |
| ~jun/2027 | Dados finais da janela prospectiva → submissão do Artigo 1 (benchmark) |

## Decisions Log

| ID | Topic | Decision | Rationale | Source | Date |
|---|---|---|---|---|---|
| D1 | Análise do código | Analisar MapaSegurancaSP diretamente | Usuário apontou os dados | Interview | 2026-10-14 |
| D2 | Natureza JEV/Laya | Modelos de decisão tipada (noul/choice/score) com probabilidades; Laya = encoder ModernBERT 421M, pesos abertos, contexto 512/1024; não são modelos espaço-temporais, então o estado é serializado em texto | Documentação oficial e da comunidade | Interview | 2026-10-14 |
| D3 | Papel do modelo de decisão | Camada final sobre features de outras áreas, comparada a baselines; e "decisão celular" na Etapa 2 | Sem baseline não há afirmação científica | Interview | 2026-10-14 |
| D4 | Próximo passo | Primário: P(desfecho no próximo período) por setor; secundário: transição de tipo de lote contra Markov/CellRank | Analogia de destino celular | Interview | 2026-10-14 |
| D5 | Desfechos | Roubo/furto de celular; violência letal (ver D20) | Dinâmicas opostas | Interview | 2026-10-14 |
| D6 | Genes vs desfecho | Genes = covariáveis (tipos definidos sem crime); histórico de crime = 2ª modalidade só nos modelos preditivos, com ablação | Evita circularidade | Interview | 2026-10-14 |
| D7 | Dados para APIs externas | Superado por D24. Regra mantida: só saem da máquina dados agregados ou anônimos | Privacidade | Interview | 2026-10-14 |
| D8 | Publicações | Data science = benchmark; Ciências urbanas = atlas | Evita salami slicing | Interview | 2026-10-14 |
| D9 | Stack | Python 3.12 (conda) + R pontual (R-INLA, spdep, scoringRules, surveillance), com Parquet como interface | Melhor ferramenta para cada tarefa | Interview | 2026-10-14 |
| D10 | Validação | 2026 lacrado até o pré-registro no OSF; tuning em 2025 com origem móvel; janela prospectiva nov/2026–mar/2027 | Blindagem contra "olharam o teste" | Interview | 2026-10-14 |
| D11 | Ética | Prevenção/planejamento; auditoria de equidade; mapas públicos agregados | Loops de feedback | Interview | 2026-10-14 |
| D12 | Seleção de covariáveis | Pool T1+T2; núcleo teórico pré-registrado; SHAP/stability selection só até 2025 com CV bloqueada; HVG/SVG não supervisionados | Não contaminar o teste | Interview | 2026-10-14 |
| D13 | Unidades | Célula = lote fiscal (+ FCU); spot = setor 2022; órgão = distrito. Celular: setor × mês; violência letal: distrito × trimestre | Unidades orgânicas, que permitem atribuição | Interview | 2026-10-14 |
| D14 | Privacidade | Excluir violência doméstica; microdados só locais; saídas agregadas; retenção até publicação + 5 anos | Bloqueio LGPD resolvido | Interview | 2026-10-14 |
| D15 | Histórico | Pré-2022 só para violência letal (SPSafe, CEM); celular a partir de 2022 | Esparsidade | Interview | 2026-10-14 |
| D16 | Geocodificação 2026 | Reconciliação hierárquica distrito × fração do setor | Cobertura de 80% para 90% em abr/2026 | Interview | 2026-10-14 |
| D17 | Escopo do atlas | Corpo: tipagem, atribuição, nichos/domínios, SVG, destino. Suplementar: comunicação célula-célula, MISTy, imagem | Foco | Interview | 2026-10-14 |
| D18 | Ingestão | Ingestão própria dos xlsx brutos; novo download de ago–set/2026; snapshot com sha256 | Parquets do Mapa sem NOME_DELEGACIA | Interview | 2026-10-14 |
| D19 | Specs | 4 specs + red-team | Mais de 8 áreas de cobertura | Interview | 2026-10-14 |
| D20 | Violência letal | Composto (homicídio doloso + tentativa + latrocínio + lesão seguida de morte) como primário; CVLI estrito como sensibilidade; mapas com taxa suavizada | Poder estatístico | Red Team | 2026-10-14 |
| D21 | Deconvolução → atribuição | Composição conhecida → taxas por tipo (Poisson com abundâncias fixas + efeito espacial) | Deconvolução clássica seria um erro conceitual | Red Team | 2026-10-14 |
| D22 | Genes por escala | Lote: atributos nativos; setor: Censo, IPVS, VIIRS, SP156, Metrô, composição | Evita que os tipos virem clusters de setores | Red Team | 2026-10-14 |
| D23 | Destino celular | Transição semestral do tipo de lote; tipo = estoques + IPTU defasado; famílias "atividade" e "cadastro" | Evita trivialidade e o artefato anual | Red Team | 2026-10-14 |
| D24 | Modelo de decisão | Só Laya; fine-tuning (RLCD) até 2024 + recalibração isotônica em 2025; zero-shot como referência; IDs anônimos + ablação com nomes reais; estado comprimido em inglês; LightGBM recebe também o estado comprimido | Reprodutível, sem custo, sem enviar dados a terceiros | Red Team | 2026-10-14 |
| D25 | Protocolo de previsão | Parâmetros congelados no fim de 2025; lags atualizados mês a mês (regra as-of); h=1 primário, h=3/6 secundários | Quebra de nível em 2026 sem vazamento | Red Team | 2026-10-14 |
| D26 | Teste primário | Jan–set/2026 = validação principal, com exposição declarada; janela prospectiva = confirmação | O usuário já viu 2026 | Red Team | 2026-10-14 |
| D27 | Reconciliação | Estratificada por tipo de local + novo geocoding (CNEFE/OSM) | Estações têm só 29,5% com coordenadas | Red Team | 2026-10-14 |
| D28 | Segredos | `.env` fora do git, limite de gasto, zero-retention (inativo após D24) | Bloqueio de segurança | Red Team | 2026-10-14 |
| D29 | Validação da atribuição | Pontos geocodificados → lote/tipo mais próximo → comparação com as taxas estimadas | Falácia ecológica | Red Team | 2026-10-14 |
| D30 | Colab | Todas as análises em GPU no Colab; só dados agregados e anônimos sobem | GPU local de 4 GB | Red Team | 2026-10-14 |
| D31 | Janela do destino | Treino 2012-S1 → 2025-S2; teste 2025-S2 → 2026-S1; alvarás só como contexto | Genes consistentes desde 2012 | Red Team | 2026-10-14 |
| D32 | Momento do pré-registro | F4 depende só de F0: registrar até 31/out/2026 com emendas datadas permitidas até abrir 2026 | O pipeline F1–F3 não fica pronto antes do início da janela prospectiva | Red Team | 2026-10-14 |
| D33 | Registro no OSF | Adiado para a etapa final, junto com os artigos. Antes de abrir 2026, um commit de congelamento (hashes dos modelos, melhores da classe) vira a chave do cofre (`FREEZE-<sha>`); 2026 é reportado como teste retrospectivo lacrado; a janela prospectiva é o teste totalmente limpo | Decisão do autor: campos do artigo só no fim. Custo aceito: sem carimbo externo de data antes da análise | Interview | 2026-10-14 |

## Dependency Graph & Implementation Order

```
F0 specs + repo
 ├─► F4 rascunho do pré-registro → congelamento antes de abrir 2026 (OSF no fim, D33) ┐
 └─► F1 ingestão BO (spec-dados)                                                    │
      └─► F2 unidades + reconciliação (spec-dados)                                  │
           └─► F3 covariáveis as-of (spec-dados)                                    │
                ├─► F5 benchmark até 2025 (spec-benchmark) ─┬─► F7 avaliação 2026 + prospectiva
                └─► F6 atlas (spec-atlas) ──────────────────┘        (hipótese-ponte)
```

1. **F0:** repositório, specs, ambiente conda e renv, esqueleto do pacote `cityomics`, testes de privacidade.
2. **F1–F3:** pipeline de dados. Bloqueia todo o resto.
3. **F4:** pré-registro logo depois de F0, porque a janela prospectiva começa em nov/2026 e o pipeline F1–F3 não termina antes disso. Ele fixa desfechos, unidades, modelos, métricas e hipóteses; detalhes de implementação entram como emendas datadas até a primeira leitura de `sealed_2026/`.
4. **F5 e F6:** em paralelo. F6 fornece as features de omics que F7 usa para a hipótese-ponte.
5. **F7:** abertura única de 2026; a janela prospectiva fecha em ~jun/2027.

## Tarefas (checklist)

### F0 — Specs e repositório
- [x] Escrever specs (overview, dados, benchmark, atlas) e estado da entrevista
- [x] `git init` + `.gitignore` (data/, .env, formatos de dados)
- [x] `environment.yml` (Python 3.12) e `R/install.R` (INLA, spdep, scoringRules, surveillance, ETAS)
- [ ] Criar o ambiente conda e congelar versões (`conda-lock`, `renv::snapshot()`)
- [x] Esqueleto do pacote `src/cityomics/` + CLI `cityomics` (typer) + cofre `sealed.py`
- [x] `tests/test_privacy.py` (colunas proibidas e padrões de chave) + `tests/test_sealed.py` + `.env.example`
- [x] README com política de retenção (publicação + 5 anos)

### F4 — Pré-registro (rascunho pronto; congelamento antes de abrir 2026; OSF na etapa final, D33)
- [x] Redigir o pré-registro a partir de spec-benchmark §5 e spec-atlas §5 (`prereg/preregistration.md`)
- [ ] Preencher autores, afiliação e parecer/dispensa do comitê de ética
- [x] Análise de poder da violência letal (proxy DP × trimestre; `prereg/analysis/`)
- [x] Declarar a exposição prévia a 2026 (site do MapaSegurancaSP)
- [ ] Commit de congelamento antes de abrir 2026: hashes dos modelos + melhores da classe → `prereg/UNSEAL_KEY`
- [ ] (Etapa final) Registrar no OSF e acrescentar o DOI

### F1 — Ingestão de BO
- [ ] `ingest/snapshot.py`: novo download de 2025–2026, cópia de 2022–2024, `snapshot.json` com sha256
- [ ] `ingest/ssp.py`: harmonização de schema 2022 / 2023+ / 2026, fórmulas Excel, chave de BO
- [ ] `ingest/celulares.py`: deduplicação por BO e VERSAO, só subtrações consumadas
- [ ] Desfechos: celular; violência letal composta; CVLI estrito
- [ ] Regra as-of (data do fato e data de registro)
- [ ] `sealed.py` + cofre `data/sealed_2026/`
- [ ] `ingest/spsafe.py`, `ingest/cem.py` (histórico de violência letal)
- [ ] Teste: totais mensais iguais aos da API SSP (±0,5%)

### F2 — Unidades e reconciliação
- [ ] Malha de setores 2022, distritos, grade de 200 m
- [ ] Lotes GeoSampa + IPTU/TPCL anual + pseudo-lotes FCU (verificar a contagem de lotes)
- [ ] `assign.py`: ponto → setor/distrito/lote mais próximo
- [ ] Novo geocoding (CNEFE/OSM) dos registros com logradouro e sem coordenadas
- [ ] `reconcile.py` estratificado por tipo de local + teste da invariante

### F3 — Covariáveis
- [ ] T1: Censo 2010/2022 (grade + Δ), IPVS, ITBI, IPTU, VIIRS C2, Metrô, OSM/ohsome, clima e calendário
- [ ] T2: CNPJ por CNAE (estoques e fluxos), SP156, alvarás, BCB
- [ ] `asof.py` com defasagens de publicação + teste
- [ ] Atualização dasimétrica da população

### F5 — Benchmark (até 2025)
- [ ] `eval/` (hit rate, PAI, PEI, CRPS, Brier, PIT, DM, equidade) testado em 2025
- [ ] Baselines (persistência, sazonal, média, STKDE, NB-GLM)
- [ ] Famílias de outras áreas: Hawkes/ETAS, BYM2 (R-INLA), MaxEnt, LGCP, GWR/painel, near-repeat
- [ ] LightGBM (features completas + estado comprimido) e seleção de covariáveis teórica vs guiada por dados
- [ ] Chronos/TimesFM e GNN (Colab)
- [ ] `laya/serialize.py` + Laya zero-shot + fine-tuning RLCD (Colab) + recalibração isotônica
- [ ] Ablações (nomes reais, sem histórico de crime, sem cada família) + ensemble → congelar

### F6 — Atlas
- [ ] `build_adata.py` (MuData lote/setor por semestre, 2012-S1 → 2026-S1)
- [ ] Tipagem Leiden/scVI vs k-means (OAC); estabilidade (ARI)
- [ ] Atribuição por tipo (Poisson com abundâncias fixas + BYM2) + validação pontual
- [ ] Nichos e domínios (Squidpy, CellCharter, Banksy) vs CLQ, SKATER, max-p
- [ ] SVG (nnSVG, SPARK-X, Hotspot) vs Moran's I
- [ ] Destino semestral: Markov, CellRank, LightGBM, Laya ZS/FT (amostra estratificada)
- [ ] Suplementares: MISTy, COMMOT (OD 2017), predição por imagem

### F7 — Avaliação e artigos
- [ ] Abrir 2026 uma única vez; métricas, mês a mês, equidade
- [ ] Hipótese-ponte (features omics no melhor modelo)
- [ ] Redigir e submeter o Artigo 2 (atlas), por volta de mar/2027
- [ ] Coletar dados prospectivos finais (~jun/2027) → submeter o Artigo 1 (benchmark)
