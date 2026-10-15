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

## Rodada consolidada com ensemble (`benchmark_run.run(table, "dev")`)

Mesma tabela de modelagem, mesmo protocolo para todos (ajuste 2023-01..2024-12, avaliação 2025, h = 1). O ensemble tem pesos ajustados em 2024-07..12 por modelos treinados até 2024-06 (`models/ensemble.py`), depois reaplicados aos modelos da janela de avaliação. Os números diferem na terceira casa dos da seção anterior porque os modelos foram reajustados nesta rodada.

| Modelo | CRPS | Log score | Brier | ECE | PAI 1% | PAI 5% |
|---|---|---|---|---|---|---|
| GNN | 0,5945 | 0,5494 | 0,1096 | 0,029 | 28,2 | 10,5 |
| LightGBM sem histórico de crime | 0,5997 | 0,5785 | 0,1154 | 0,055 | 26,8 | 10,2 |
| Hawkes discreto | 0,5998 | 0,5729 | 0,1151 | 0,037 | 27,7 | 10,2 |
| **Ensemble** | 0,6000 | **0,5426** | **0,1081** | 0,025 | **28,3** | **10,6** |
| LightGBM completo | 0,6026 | 0,5474 | 0,1090 | 0,026 | 28,0 | 10,6 |
| LightGBM núcleo teórico | 0,6058 | 0,5472 | 0,1089 | 0,022 | 28,3 | 10,5 |
| GWR por distrito | 0,6069 | 0,5556 | 0,1107 | 0,025 | 28,0 | 10,4 |
| Painel espacial | 0,6147 | 0,5569 | 0,1104 | 0,021 | 27,9 | 10,4 |
| GLM de contagem | 0,6193 | 0,5599 | 0,1108 | 0,024 | 27,6 | 10,4 |
| Média histórica | 0,6193 | 0,5627 | 0,1114 | 0,022 | 27,6 | 10,3 |
| BYM2 | 0,6362 | 0,5566 | 0,1102 | 0,017 | 27,5 | 10,4 |
| SPDE | 0,6558 | 0,5798 | 0,1151 | 0,016 | 25,4 | 10,0 |
| Chronos zero-shot | 0,6697 | 0,6037 | 0,1211 | 0,038 | 25,5 | 9,7 |
| MaxEnt | 0,7091 | 0,6268 | 0,1235 | 0,019 | 20,7 | 8,7 |
| STKDE | 0,7726 | 0,6701 | 0,1387 | 0,018 | 13,2 | 7,3 |

Pesos do ensemble: BYM2 0,28, GNN 0,23, LightGBM núcleo 0,22, LightGBM completo 0,20, LightGBM sem crime 0,03, Chronos 0,02, Hawkes 0,01.

Leituras:
- **O ensemble vence em log score, Brier e PAI, mas não em CRPS**: o GNN sozinho tem o menor CRPS (0,5945 contra 0,6000). O CRPS de contagens com cauda pesada premia o ajuste dos setores de estação, que o GNN captura melhor. Qual métrica decide é questão do pré-registro (o primário é CRPS), então o ensemble não pode ser apresentado como melhor modelo; ele é o melhor probabilístico em log score e calibração.
- **O BYM2 entra com o maior peso (0,28) apesar do pior CRPS individual**: ele é o mais bem calibrado e complementar aos modelos de árvore, o que o ensemble usa.
- **O ganho total sobre o baseline continua pequeno**: o melhor CRPS (GNN) é 4% menor que o do GLM/média histórica, e o log score do ensemble 3% menor.
- Falta o teste formal (bootstrap por distrito com Holm) entre os candidatos principais; ele sai na rodada de seleção para o congelamento.

## Teste formal e seleção dos melhores da classe (`models/select_run.py`)

Bootstrap por cluster de distrito (96 distritos, 2000 reamostras), Holm dentro de cada família de testes. Dados: previsões de 2025 da rodada consolidada (ajuste 2023–2024). Resultados completos em `prereg/selection_dev.json`.

**Seleção provisória (`prereg/selection.json`):**

| Chave | Escolha |
|---|---|
| Melhor baseline por CRPS | GLM de contagem (0,6193; empata com a média histórica até a 4ª casa) |
| Melhor baseline por PAI 1% | Média histórica (27,60; GLM 27,59) |
| Melhor outras áreas por CRPS | GNN (0,5945) |
| Melhor outras áreas por PAI 1% | Ensemble empilhado (28,27; LightGBM núcleo 28,26 e GNN 28,20) |
| Laya-FT, LightGBM no estado comprimido, Markov do destino | pendentes (Colab e atlas) |

**H1a (CRPS), GNN contra GLM:** diferença −0,0248 (IC 95% −0,0343 a −0,0164), p ajustado por Holm 0,001. Efeito pequeno (4%), mas distinguível do ruído quando o distrito é a unidade de reamostragem.

**H1b (PAI 1%), ensemble contra média histórica:** diferença +0,69 (IC −0,30 a +1,79), p ajustado 0,19. **Não há evidência de que o PAI a 1% melhore.** Todos os modelos fortes ficam em 27,5–28,3 porque o ranking é dominado pelos setores de estações e terminais.

**Cada modelo contra o GLM (CRPS, Holm entre os 12 modelos):**

| Modelo | Diferença | IC 95% | Holm |
|---|---|---|---|
| GNN | −0,0248 | −0,0343 a −0,0164 | sim |
| LightGBM sem crime | −0,0196 | −0,0265 a −0,0134 | sim |
| Hawkes | −0,0194 | −0,0244 a −0,0150 | sim |
| Ensemble | −0,0193 | −0,0285 a −0,0110 | sim |
| LightGBM completo | −0,0167 | −0,0250 a −0,0094 | sim |
| LightGBM núcleo | −0,0135 | −0,0217 a −0,0062 | sim |
| GWR por distrito | −0,0124 | −0,0205 a −0,0052 | sim |
| Painel espacial | −0,0046 | −0,0095 a −0,0001 | não (p 0,051) |
| BYM2 | +0,0169 | +0,0101 a +0,0228 | pior |
| SPDE | +0,0365 | +0,0316 a +0,0415 | pior |
| Chronos zero-shot | +0,0504 | +0,0448 a +0,0571 | pior |
| MaxEnt | +0,0898 | +0,0685 a +0,1125 | pior |

**Entre finalistas:** o GNN é melhor que o ensemble (−0,0055), o LightGBM completo (−0,0081) e o núcleo (−0,0113), todos com Holm significativo. **Não se distingue do Hawkes** (−0,0054, IC −0,0150 a +0,0039). Ensemble, LightGBM completo e Hawkes também empatam entre si. O núcleo teórico (71 variáveis) fica 0,0032 atrás do conjunto completo, diferença pequena mas significativa.

**Brier de P(≥1) contra o GLM:** ensemble −0,0028, LightGBM completo −0,0018, GNN −0,0013, todos com IC que exclui zero. Antecipa o terreno do H2, mas ainda sem Laya.

Cuidados:
- A seleção é **provisória**. A VIIRS (luz noturna, grupo CPTED do núcleo) ainda não está na tabela; ao incluí-la, o benchmark e a seleção são refeitos.
- Os pesos do ensemble foram ajustados em 2024-H2. No congelamento serão reajustados dentro de 2025, como o pré-registro exige.
- O bootstrap do PAI usa o hit rate agregado nos 12 meses, não a média mensal usada para escolher. As duas versões coincidem na ordem dos modelos.
- Escolher o melhor entre 12 modelos no mesmo período de avaliação infla o ganho observado em 2025. A confirmação honesta é o teste em 2026 com a escolha já congelada.
