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

## LightGBM e Hawkes em 2025 (ajuste 2023–2024, h = 1)

| Modelo | CRPS | Log score | Brier | ECE | PAI 1% | PAI 5% |
|---|---|---|---|---|---|---|
| Hawkes discreto (fundo com núcleo teórico + excitação própria e vizinha) | 0,600 | 0,573 | 0,115 | 0,038 | 27,7 | 10,2 |
| LightGBM completo (319 variáveis) | 0,602 | 0,549 | 0,109 | 0,027 | 27,9 | 10,5 |
| LightGBM sem histórico de crime (298) | 0,603 | 0,592 | 0,115 | 0,055 | 26,8 | 10,3 |
| LightGBM núcleo teórico + histórico (71) | 0,608 | 0,549 | 0,109 | 0,024 | 28,2 | 10,5 |
| LightGBM só histórico (23) | 0,613 | 0,553 | 0,110 | 0,021 | 27,9 | 10,5 |
| GLM de contagem (baseline) | 0,618 | 0,560 | 0,111 | 0,024 | 27,6 | 10,4 |

Leituras:
- **Ganho pequeno sobre o melhor baseline.** O CRPS do melhor modelo (0,600) é cerca de 3% menor que o do GLM (0,618), e o log score do LightGBM completo (0,549) 2% menor. O sinal já está quase todo na média longa de cada setor.
- **Covariáveis sozinhas quase igualam o histórico.** O LightGBM sem nenhum histórico de crime tem CRPS praticamente igual ao completo (0,603 contra 0,602), embora pior em log score e calibração. As covariáveis mais importantes dele são SP156 de população em situação de rua, número de pontos de iluminação, bares e restaurantes (CNPJ) e densidade populacional, que funcionam como proxy do padrão de uso do espaço. Isso é a ablação D6: a circularidade com o histórico de crime não explica o desempenho.
- **Núcleo teórico (71 variáveis) perde pouco** para o conjunto completo (0,608 contra 0,602 em CRPS; log score igual).
- **Excitação no Hawkes:** a própria vizinhança quase não contribui (pesos ≈ 0,003 contra ≈ 0,13 por lag próprio), ou seja, o contágio espacial entre setores vizinhos não aparece na escala mensal.
- **PAI.** Todos os modelos fortes ficam em PAI a 1% ≈ 28, praticamente igual: o ranking dos hotspots é dominado pelos setores de estações e terminais.

## Famílias de outras áreas em 2025 (ajuste 2023–2024, h = 1)

| Modelo (origem) | CRPS | Log score | Brier | ECE | PAI 1% | PAI 5% |
|---|---|---|---|---|---|---|
| GNN espaço-temporal (grafo de 8 vizinhos, núcleo teórico) | 0,597 | 0,549 | 0,110 | 0,027 | 28,0 | 10,5 |
| LightGBM + near-repeat (completo) | 0,603 | 0,548 | 0,109 | 0,026 | 28,1 | 10,6 |
| GWR por distrito (geoeconomia) | 0,607 | 0,556 | 0,111 | 0,025 | 28,0 | 10,4 |
| Painel espacial (econometria) | 0,615 | 0,557 | 0,110 | 0,021 | 27,8 | 10,4 |
| BYM2 (epidemiologia, INLA) | 0,636 | 0,557 | 0,110 | 0,017 | 27,5 | 10,4 |
| SPDE/LGCP aproximado (INLA) | 0,656 | 0,580 | 0,115 | 0,016 | 25,4 | 10,0 |
| Chronos-Bolt small, zero-shot (séries temporais) | 0,669 | 0,604 | 0,121 | 0,039 | 25,5 | 9,7 |
| MaxEnt, background uniforme (ecologia) | 0,709 | 0,627 | 0,123 | 0,019 | 20,7 | 8,7 |

Leituras:
- **GNN** é o melhor em CRPS (0,597), mas a diferença para o Hawkes e o LightGBM (≈ 0,600–0,602) é de 0,5% e provavelmente cabe no intervalo do bootstrap por distrito; o teste formal fica para o ensemble.
- **Near-repeat** (janelas de 30/90/180 dias em 500 m e 1 km) não melhora o LightGBM (0,6034 contra 0,6020): na escala mensal por setor a vitimização repetida já está absorvida pelos lags.
- **Modelos bayesianos espaciais** são bem calibrados (ECE 0,016–0,017, os menores), mas pior em CRPS: o efeito aleatório espacial encolhe demais as taxas dos setores de estação.
- **Chronos zero-shot** perde para a média histórica: séries mensais por setor têm contagens baixas e ruído de Poisson dominante, e o modelo não conhece a covariação espacial.
- **MaxEnt** com background uniforme é fraco porque trata crime como presença sem esforço amostral; o desvio (background de grupo-alvo, como no pré-registro) fica declarado em `prereg/AMENDMENTS.md` como pendência.
