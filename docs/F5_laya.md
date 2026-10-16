# F5 — Laya no protocolo de desenvolvimento

Fine-tuning no Colab (A100), recalibração isotônica e comparação no mesmo estado. Nada de 2026 foi lido.

## Protocolo

| Etapa | Período | Linhas |
|---|---|---|
| Fine-tuning | 2024-H1 | 60.000 estados × 3 perguntas = 180.000 itens (2.000 separados para calibração) |
| Recalibração isotônica (e do LightGBM no estado) | 2024-H2 | 60.000 estados |
| Avaliação | 2025 | 81.900 estados (25% dos setores, os mesmos para todos os modelos) |

Os escores de Hawkes, BYM2, KDE e MaxEnt que aparecem no texto do estado são previsões **fora da amostra**: ajustadas só com meses anteriores ao do estado. Setores aparecem como `T-<hash>` e cada estado tem um `state_id`; o mapa para o setor fica local.

## Treino

- Base: `laya-typed-decisions` (ModernBERT-large, 421M parâmetros, contexto 1024), pacote `laya` 0.4.8.
- Alvos: desfecho observado como one-hot (P(≥1), P(≥3), faixa 0 / 1 / 2–3 / 4–7 / 8+), com suavização de rótulo de 0,05.
- Perda **soft cross-entropy** (sem o termo de política do RLCD), AdamW, taxa do encoder 1e-5 e da cabeça 5e-5, agenda cosseno, batch efetivo 32 (16 × 2), fp16, 3 épocas.
- **A primeira tentativa (RLCD padrão, taxas 2,5e-5 e 1e-4) divergiu**: perda média de 1,74, bem acima de 0,446 (entropia só com as frequências), com picos de 6 a 10. Era superconfiança. O ajuste acima corrigiu.
- Perda média por época: 0,4152, 0,4069, 0,3999. Em itens separados antes do treino: perda 0,408, ECE 0,036, acurácia 0,872 (a classe mais comum dá ≈ 0,855). Um teste curto (10 mil estados, 1 época) tinha chegado a perda 0,396 nessa mesma medida: **18× mais computação não melhorou o resultado**.

## Resultado em 2025: P(≥1), Brier

| Modelo | Brier | ECE | AUC | Log loss |
|---|---|---|---|---|
| Ensemble (NB) | **0,1074** | 0,025 | 0,839 | 0,349 |
| LightGBM no estado comprimido (recalibrado) | 0,1079 | 0,007 | 0,835 | 0,351 |
| LightGBM completo (NB) | 0,1081 | 0,026 | 0,836 | 0,351 |
| **Laya-FT (recalibrado)** | 0,1084 | 0,010 | 0,833 | 0,352 |
| Laya-FT (bruto) | 0,1087 | 0,020 | 0,833 | 0,355 |
| GLM (NB) | 0,1099 | 0,024 | 0,824 | 0,361 |
| Média histórica | 0,1105 | 0,022 | 0,818 | 0,363 |
| Laya-ZS (recalibrado) | 0,1464 | 0,010 | 0,649 | 0,463 |
| Laya-ZS (bruto) | 0,2828 | 0,365 | 0,650 | 0,759 |

## Testes pareados (bootstrap por distrito, 96 clusters, Holm entre os 6)

| Comparação (Brier) | Diferença | IC 95% | Holm |
|---|---|---|---|
| **H2: Laya-FT − LightGBM no estado** | **+0,00057** | +0,00022 a +0,00092 | sim, **a favor do LightGBM** |
| Laya-FT − Laya-ZS | −0,0379 | −0,0434 a −0,0329 | sim |
| Laya-FT − GLM | −0,0015 | −0,0020 a −0,0010 | sim |
| Laya-FT − LightGBM completo | +0,00030 | −0,00012 a +0,00073 | não |
| Laya-FT − ensemble | +0,00105 | +0,00065 a +0,00143 | sim, a favor do ensemble |
| LightGBM no estado − GLM | −0,0020 | −0,0025 a −0,0015 | sim |

## Leituras

- **H2 não é sustentado no desenvolvimento.** O Laya-FT ajustado não bate o LightGBM no mesmo estado comprimido. A diferença é minúscula (0,0006 em Brier, 0,5%), mas distinguível do ruído e no sentido do LightGBM. O pré-registro prevê teste bilateral, e este seria o resultado esperado se H2 fosse rejeitado.
- **O Laya-FT é um bom decisor probabilístico**: supera o GLM e o baseline, empata com o LightGBM completo e fica bem calibrado depois da recalibração isotônica (ECE 0,010). O que não faz é superar um modelo de árvore que enxerga as mesmas informações.
- **O zero-shot não serve.** Mesmo recalibrado, fica pior que a média histórica (0,146 contra 0,110; AUC 0,65). O texto serializado sozinho, sem ajuste, não dá ao modelo a capacidade de prever.
- **O estado já carrega a previsão dos outros métodos.** Hawkes, BYM2, KDE e MaxEnt entram no texto, então Laya-FT e LightGBM no estado são, em parte, empilhadores desses escores. O ensemble puro (pesos ajustados por log score) continua à frente de ambos.
- O ganho de qualquer modelo sobre o GLM é pequeno (1 a 2% em Brier), o que combina com o resultado do benchmark.

## Pendências

- Ablações do estado: nomes reais (conhecimento prévio do modelo), sem histórico de crime, sem cada bloco de escores.
- Avaliar também P(≥3) e a faixa de contagem (as respostas já estão nos CSVs).
- Hash dos pesos (`sha256` do `model.safetensors`) para o manifesto de congelamento.
- No protocolo final, o ajuste usa ≤ 2024 e a recalibração 2025; o resultado de desenvolvimento acima não decide a escolha, só o desenho.
