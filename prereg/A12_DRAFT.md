# A12: correção do CRPS com contagem fracionária — vigente: datada em 2026-10-27; `selection.json` aplicado

> Rascunho de 2026-10-20, preparado sob delegação durante a revisão pelo parecer crítico. **Não vale até o autor revisar, datar e copiar a linha final para `AMENDMENTS.md`, antes do FREEZE-A.** Nenhum dado de 2026 foi usado.

## Problema

O §5.3 e a emenda A6 fixam o CRPS "contra y real" (a contagem reconciliada fracionária) pela fórmula

    Σₖ (F(k) − 1{k ≥ y})²,  k = 0, 1, 2, …

Essa soma só é o CRPS quando y é inteiro. Quando y é fracionário, ela devolve o CRPS de ⌈y⌉: uma contagem de 0,03 é pontuada como um evento.

Em 2025, 65% dos setor × mês têm contagem fracionária, e 48% ficam entre 0 e 1.

O erro foi conferido por três caminhos, que concordam (`data/processed/atlas/fenotipo/reconciliacao.json`, bloco `crps_verificacao`):
- a integral numérica;
- a amostragem de E|X − y| − ½E|X − X′|;
- a forma fechada abaixo.

## Correção

O CRPS é ∫ (F(x) − 1{x ≥ y})² dx. Para y em [j, j + 1), a forma fechada é a interpolação linear entre o CRPS de ⌊y⌋ e o de ⌈y⌉:

    CRPS(y) = CRPS(⌈y⌉) − (⌈y⌉ − y)·(2F(⌊y⌋) − 1)

Implementação:
- `cityomics.eval.scores.crps_nb` passa a calcular essa forma, com testes contra a definição;
- `crps_nb_registrado` guarda a fórmula anterior, para reproduzir os números já publicados.

As demais métricas não mudam: log score em y arredondado, Brier de y ≥ 0,5, PAI e captura.

## Consequências no desenvolvimento (2025, previsões gravadas, 96 distritos)

`python -m cityomics.models.repontua_crps` refaz os escores e `prereg/selection_dev.json`. A versão anterior fica em `selection_dev_crps_registrado.json`.

| Modelo | Fórmula registrada | CRPS corrigido |
|---|---|---|
| GNN − GLM | −0,025 (−0,034 a −0,016), −4,0% | −0,011 (−0,017 a −0,007), −4,5% |
| LightGBM núcleo − GLM | — | −0,012 (−0,018 a −0,008), −4,9% (melhor modelo único) |
| Ensemble − GLM | −0,019, −3,1% | −0,016 (−0,023 a −0,011), −6,4% (primeiro no ranking) |
| Hawkes e LightGBM sem crime | melhores que o GLM | piores que o GLM |

O H1a de desenvolvimento continua apoiado (p ajustado = 0,001). O melhor modelo de outras áreas passa a ser o ensemble.

## Decisões do autor

1. **Métrica.** Adotar o CRPS corrigido como métrica do H1a. A alternativa é o CRPS sobre y arredondado, que dá praticamente o mesmo ranking.
2. **Seleção.** Refazer a seleção dos melhores da classe com a métrica escolhida. `prereg/selection.json` **não foi alterado** e hoje aponta `lgbm_sem_crime`, que vem da rodada com VIIRS. Nas previsões de desenvolvimento, sem VIIRS, esse modelo fica em 11º com o CRPS corrigido e pior que o GLM.
3. **Rodada VIIRS.** Repontuada em 2026-10-26 (`python -c "from cityomics.models import repontua_crps as r; r.run('viirs')"`); a versão anterior está em `prereg/selection_viirs_crps_registrado.json`. O resultado repete o do desenvolvimento:
   - ensemble em primeiro: −0,015 contra o GLM (−0,022 a −0,010; p ajustado = 0,001);
   - LightGBM núcleo e GNN em seguida: −0,012 e −0,011;
   - `lgbm_sem_crime`, hoje em `selection.json`, fica **pior** que o GLM: +0,013 (+0,007 a +0,020);
   - H1b continua nulo: p = 0,22.

   **Proposta para `selection.json`**, a aplicar só quando o autor datar esta emenda: `best_crossdomain_crps` passa de `lgbm_sem_crime` para `ensemble`. As outras três entradas não mudam: `glm`, `media_historica` e `ensemble`.
4. **Pesos do ensemble.** Não mudam: foram ajustados pela deviance de Poisson, não pelo CRPS.
