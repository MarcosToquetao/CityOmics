# A11 — RASCUNHO (não vigente até o autor datar e mover para AMENDMENTS.md)

> Preparado em 2026-10-16, sob delegação, a partir das decisões D34–D62 (`spec-figuras.md`). Nada aqui vale até o autor revisar, datar e copiar a linha final para `AMENDMENTS.md` **antes do FREEZE-B**. Os números citados são do desenvolvimento (2022–2025, fora do cofre espacial).

## 1. Calendário do congelamento (D52)

- **FREEZE-A** (até o início de dez/2026): benchmark (seleção já em `prereg/selection.json`) e features mínimas do atlas para H3.
  - O manifesto passa a incluir os hashes de `lote_tipos_2025.parquet`, `setor_dominio_2025.parquet`, `setor_composicao_2025.parquet`, `prereg/atlas_vault.json` e `src/cityomics/atlas/lr_pairs.json` (`freeze.ATLAS`).
- **FREEZE-B** (antes de abrir 2026): esta emenda (escolhas descritivas e lista do multiverso) e o resultado da confirmação no cofre espacial.
- **Janela prospectiva** (nov/2026–mar/2027): os meses já publicados até o FREEZE-B são declarados expostos.
- **Violência letal de 2026:** rotulada como exposta (o site do autor mostra 2026 por distrito e mês; D61).

## 2. Tipagem fixada sem crime (D38, D53)

- **Genes do lote** (30): IPTU 2025 (uso, padrão, pavimentos, unidades, áreas, valores, idade, testada, esquina) e CNPJ ativo no snapshot 2025-12, ligado por endereço (11 grupos de CNAE + MEI).
- **PCA e Leiden:** PCA com 15 componentes; Leiden com resolução 0,02, a mais estável com 10 a 16 tipos (ARI de 0,973 entre 8 subamostras de 80 mil lotes). Referência de 80 mil lotes estratificada por distrito e transferência kNN.
- **Ajustes:** tipos com menos de 0,3% fundidos; sub-agrupamento vertical por regra de genes (≥ 4 pavimentos ou ≥ 8 unidades no tipo misto) → 12 tipos, mais favelas FCU e lotes sem cadastro.
- **Hash:** o de `lote_tipos_2025.parquet` entra no FREEZE-A.

## 3. Cofre espacial e família do atlas (D53)

- **Cofre:** 19 dos 96 distritos (semente 20261016; sha256 em `prereg/atlas_vault.json`), excluídos de toda análise de crime do atlas.
- **Confirmação:** roda **uma vez** nos distritos do cofre depois desta emenda e antes do FREEZE-B. 2026 vira teste de estabilidade.
- **Família do atlas** (Holm próprio, α = 0,05). Candidatas a escolher pelo autor:
  1. **A-R1:** o ranking das taxas atribuídas por classe de célula se repete no cofre (Spearman ≥ 0,7 com o desenvolvimento).
  2. **A-R2:** validação pontual no cofre (Spearman entre taxa atribuída e observada > 0; dev = 0,93).
  3. **A-R3:** o melhor par ligante → receptor tem ganho fora da amostra > 0 contra o lag do ligante no cofre.
  4. **A-R4:** a excitação cruzada (Knox) comércio → comércio tem razão > 1 no cofre.
  5. **A-R5:** o tecido (tipos + domínios + ruas) explica a taxa do setor além dos mesmos genes agregados sem tipagem (comparador de H3).

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
| (data) | 3.4, 5.2, 7 | A11. Integrated paper (D34). Two-stage freeze (FREEZE-A: benchmark + atlas labels by hash; FREEZE-B: this amendment). Atlas typing fixed without crime (Leiden r = 0.02, 12 types + FCU favelas). Spatial vault of 19 districts with a separate Holm family for atlas claims (A-R1…A-R5). H3 compares atlas features against the same lot genes aggregated without typing. H4 per option (a)/(b). Lethal 2026 declared exposed | Red-team review of 2026-10-16 (D51–D62) |
