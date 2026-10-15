# F5: benchmark (até 2025)

Resultados no período de tuning: **ajuste em 2024, avaliação em 2025, h = 1**, setor × mês, observação reconciliada (`n_total`). Nada de 2026 foi lido.

## Componentes prontos

- **`eval/`**: CRPS da NB2 contra observação real (verificado contra a definição `E|X−y| − ½E|X−X'|`), log score, Brier de P(≥1) com decomposição, PAI/PEI/hit rate por mês, PIT randomizado, reliability e ECE, bootstrap por cluster (distrito) e Holm, auditoria de equidade.
- **`features/history.py`**: histórico de crime **as-of exato**. O lag `L` do mês `m` conta só os eventos de fato em `m − L` já registrados antes de `m` (7% dos BOs são registrados no mês seguinte). O histórico por setor usa só eventos geocodificados e é corrigido pela cobertura geocodificada do distrito, para a alta de 80% para 90% da cobertura não parecer alta de crime. Testado: remover eventos registrados depois do início de `m` não muda a linha de `m`.
- **`features/table.py`**: tabela setor × mês 2022–2025 (1.310.448 linhas) com alvo, histórico, vizinhança espacial (8 vizinhos por centroide) e as covariáveis numéricas do painel.
- **`models/baselines.py`**: persistência, sazonal ingênuo, média histórica, STKDE, hotspotting prospectivo e GLM de contagem. Todos passam pela mesma calibração (`mu = a·x + b`, dispersão NB, total do período de ajuste preservado).

## Baselines em 2025 (h = 1)

| Modelo | CRPS | Log score | Brier P(≥1) | ECE | PAI 1% | PAI 5% |
|---|---|---|---|---|---|---|
| GLM de contagem | 0,618 | 0,560 | 0,111 | 0,024 | 27,6 | 10,4 |
| Média histórica (12 m) | 0,629 | 0,562 | 0,111 | 0,018 | 27,6 | 10,3 |
| STKDE | 0,694 | 0,616 | 0,125 | 0,026 | 22,6 | 9,6 |
| Persistência | 0,706 | 0,655 | 0,133 | 0,038 | 22,1 | 8,5 |
| Sazonal ingênuo | 0,723 | 0,663 | 0,134 | 0,034 | 21,5 | 8,3 |
| Hotspotting prospectivo | 0,772 | 0,669 | 0,139 | 0,021 | 13,6 | 7,4 |

Leituras: a média de 12 meses e o GLM vencem de longe a persistência, o que mostra que a série mensal por setor é ruidosa e o sinal está na média longa. A largura de banda ótima do STKDE no ajuste ficou em 100 m (o menor da grade), ou seja, a suavização espacial não ajuda aqui. O PAI a 1% é alto (≈ 27) porque a observação reconciliada concentra os roubos de celular em setores de estações e terminais.
