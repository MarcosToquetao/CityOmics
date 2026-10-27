# A11 — vigente: datada pelo autor em 2026-10-27 (linha em AMENDMENTS.md; família B, A-R5 exploratória)

> Preparado em 2026-10-16 e atualizado em 2026-10-26 (tipagem refeita, C5 redefinida, ensaio refeito), sob delegação, a partir das decisões D34–D62 (`spec-figuras.md`). Nada aqui vale até o autor revisar, datar e copiar a linha final para `AMENDMENTS.md` **antes do FREEZE-B**. Os números citados são do desenvolvimento (2022–2025, fora do cofre espacial).

## 1. Calendário do congelamento (D52)

- **FREEZE-A** (até o início de dez/2026): benchmark (seleção já em `prereg/selection.json`) e features mínimas do atlas para H3.
  - O manifesto passa a incluir os hashes de `lote_tipos_2025.parquet`, `setor_dominio_2025.parquet`, `setor_composicao_2025.parquet`, `prereg/atlas_vault.json` e `src/cityomics/atlas/lr_pairs.json` (`freeze.ATLAS`).
- **FREEZE-B** (antes de abrir 2026): esta emenda (escolhas descritivas e lista do multiverso) e o resultado da confirmação no cofre espacial.
- **Janela prospectiva** (nov/2026–mar/2027): os meses já publicados até o FREEZE-B são declarados expostos.
- **Violência letal de 2026:** rotulada como exposta (o site do autor mostra 2026 por distrito e mês; D61).

## 2. Tipagem fixada sem crime (D38, D53; refeita em 2026-10-20)

- **Genes do lote** (30): IPTU 2025 (uso, padrão, pavimentos, unidades, áreas, valores, idade, testada, esquina) e CNPJ ativo no snapshot 2025-12, ligado por endereço (11 grupos de CNAE + MEI).
- **PCA e Leiden:** PCA com 15 componentes (81,5% da variância); Leiden com resolução 0,02, a mais estável com 10 a 16 tipos (ARI de 0,950 entre 8 subamostras de 80 mil lotes). O kNN é exato (scikit-learn), o que deixa os rótulos determinísticos. Referência de 80 mil lotes estratificada por distrito e transferência kNN.
- **Ajustes:** tipos com menos de 0,3% fundidos ao centróide mais próximo; regra vertical sem crime em todos os tipos (≥ 4 pavimentos ou ≥ 8 unidades viram o tipo "Vertical residencial e misto") → 16 tipos, mais favelas FCU e lotes sem cadastro. Tipos com o mesmo nome-base recebem o qualificador do atributo em que mais excedem o maior do grupo (`typing.QUALIFICADORES`).
- **Por que foi refeita:** a tipagem anterior (12 tipos, ARI de 0,973) tinha sido calculada numa versão da tabela de lotes anterior à unificação dos polígonos repetidos (1.687.685 lotes) e não se reproduzia com a tabela atual (ARI de 0,58). A versão anterior está preservada em `data/processed/_versoes/`.
- **Hash:** o de `lote_tipos_2025.parquet` entra no FREEZE-A.

## 3. Cofre espacial e família do atlas (D53; atualizado para a narrativa B, D63, D68)

- **Cofre:** 19 dos 96 distritos (semente 20261016; sha256 em `prereg/atlas_vault.json`), excluídos de toda análise de crime do atlas.
- **Confirmação:** roda **uma vez** nos distritos do cofre, depois desta emenda datada em `AMENDMENTS.md` e antes do FREEZE-B, com `cityomics.atlas.confirmacao.confirmar()`. O código recusa rodar sem a A11 datada e recusa rodar uma segunda vez (`prereg/atlas_confirmacao.json`). 2026 vira teste de estabilidade.
- **Desenvolvimento × teste:** o desenvolvimento são os 77 distritos de exploração; o teste, os 19 do cofre. Cada afirmação tem estatística, p unilateral e critério de efeito; é sustentada se o p ajustado por Holm < 0,05 **e** o critério é cumprido.
- **Família recomendada para a narrativa B** (Holm próprio, α = 0,05), escolha final do autor:

  | ID | Afirmação | Estatística | Critério | Ensaio (pseudo-cofre) |
  |---|---|---|---|---|
  | **A-R1** | O ranking das taxas atribuídas por classe (celular 2025) se repete | Spearman dev × teste (permutação das classes) | ρ ≥ 0,7 | 0.91 (p de Holm 0.001; sustentada) |
  | **A-R2** | Validação pontual no teste | Spearman(λ do teste, taxa observada por ponto) | ρ > 0 | 0.46 (p de Holm 0.040; sustentada) |
  | **A-R6** | As assinaturas classe × fenótipo se repetem | mediana do Spearman das participações (fenótipos com ≥ 200 eventos no teste) | ≥ 0,7 | 0.85 (p de Holm 0.001; sustentada) |
  | **A-R7** | O relógio do furto de celular difere entre classes | contraste H (2024–2025) contra 999 permutações dos períodos dentro do distrito | p < α | 0.21 (p de Holm 0.003; sustentada) |
  | **A-R8** | Na queda 2022→2025, os polos perdem menos que as ruas locais | log(razão) do crime atribuído aos polos (estações, terminais, comércio e serviços, pela família da tipagem) − log(razão) das ruas locais (bootstrap por distrito) | > 0 | 0.73 (p de Holm 0.002; sustentada) |

- **Fora da família de B:**
  - **A-R5** (tecido além dos genes sem tipagem, comparador de H3): opcional; no ensaio, ΔR² = -0.015 (p = 0.80), coerente com o desenvolvimento (a tipagem interpreta, não prevê). Se entrar, consome α sem expectativa de sucesso;
  - **A-R3** (melhor par L–R) e **A-R4** (Knox comércio → comércio): a comunicação vai para o Extended Data na narrativa B; ficam exploratórias.
- **Ensaio (pseudo-confirmação, D53):** `confirmacao.ensaiar()` sorteia 19 distritos de exploração como pseudo-cofre (semente 1) e roda as seis afirmações acima, A-R5 incluída (Holm sobre seis, mais conservador que a família de B); resultado em `data/processed/atlas/confirmacao_ensaio.json`. Não lê o cofre.
- **Dados novos da narrativa B:** Pesquisas Origem-Destino 2017 e 2023 do Metrô (`data/external/od/OD-2017.zip`, baixada em 2026-10-19, e `OD-2023-zip/Site_190225_PesquisaOD2023.zip`, sha256 1844d38a…, baixada em 2026-10-20, ambas com autorização do autor; a 2023 é a principal); painel de 15 fenótipos da base principal da SSP (D64). Os alvos dos fenótipos, a presença da OD e o código da confirmação entram no manifesto do FREEZE (`freeze.ATLAS`).

## 4. H3 e H4 (D55, D42)

- **H3:** o modelo do benchmark com as features do atlas (tipo, domínio, composição) é comparado com o **mesmo modelo** com os genes do lote agregados por setor, sem tipagem. Ambos ficam congelados no FREEZE-A.
- **H4** — escolher uma opção:
  - (a) redefinida sobre as transições anuais de família pelo IPTU (2012–2025, sem 2021), com o Laya no destino no suplemento, mantendo o Holm com 5 testes;
  - (b) rebaixada a exploratória, com Holm sobre 4 testes (H1a, H1b, H2, H3).

## 5. Comunicação: tabela multiverso (D39, D40)

Todas as abordagens rodadas ficam na tabela multiverso do suplemento (`data/processed/atlas/comunicacao/multiverso.parquet` → ED2). As que entram no corpo do artigo são as escolhidas pelo autor nesta seção, e só elas são confirmadas no cofre (A-R3, A-R4).

## Linha proposta para AMENDMENTS.md

| Date | Section | Change | Reason |
|---|---|---|---|
| (data) | 3.4, 5.2, 7 | A11. Integrated paper (D34) with narrative B (D63): crime as a phenotype of urban tissue. Atlas family for B: A-R1, A-R2, A-R6 (phenotype signatures), A-R7 (tissue clock), A-R8 (hubs fall less than local streets), Holm, one-shot confirmation in the spatial vault with pre-specified code (`atlas/confirmacao.py`); A-R3/A-R4 exploratory; A-R5 optional. New data: OD 2023 survey (ambient population; 2017 as sensitivity). Two-stage freeze (FREEZE-A: benchmark + atlas labels by hash; FREEZE-B: this amendment). Atlas typing fixed without crime (Leiden r = 0.02 on an exact kNN graph, 16 types + FCU favelas; recomputed 2026-10-21). Spatial vault of 19 districts with a separate Holm family for atlas claims (A-R1…A-R5). H3 compares atlas features against the same lot genes aggregated without typing. H4 per option (a)/(b). Lethal 2026 declared exposed | Red-team review of 2026-10-16 (D51–D62) |
