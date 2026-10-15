# Pré-registro

| Arquivo | Conteúdo |
|---|---|
| `preregistration.md` | Rascunho do pré-registro no modelo do OSF para dados secundários, em inglês |
| `core_covariates.json` | Núcleo teórico de covariáveis, fixado antes de qualquer modelo |
| `selection.json` | (a criar na F5) identidades dos melhores da classe, escolhidas só com 2025 |
| `FREEZE_MANIFEST.json` | (gerado por `cityomics freeze commit`) hashes de entradas, locks, modelos e seleção |
| `AMENDMENTS.md` | Emendas datadas, permitidas até a primeira abertura do cofre de 2026 |
| `analysis/` | Análise de poder da violência letal (código e saída; só dados de 2022–2025) |
| `UNSEAL_KEY` | Chave do cofre de 2026: `FREEZE-<sha>` do commit de congelamento e, na etapa final, o DOI do OSF |

## Calendário (D33)

O registro no OSF fica para a etapa final, junto com os artigos. Até lá:

- o rascunho evolui aqui, com mudanças anotadas em `AMENDMENTS.md`;
- **antes de abrir os dados de 2026**, um commit de congelamento registra os hashes dos modelos e a seleção dos melhores da classe, e `UNSEAL_KEY` recebe `FREEZE-<sha>` desse commit;
- 2026 entra no artigo como teste retrospectivo lacrado, e a janela prospectiva (nov/2026–mar/2027) como o teste totalmente limpo.

## Como congelar (antes de abrir 2026)

1. Termine a F5 com os modelos finais salvos em `data/models/frozen/` e crie `prereg/selection.json` com as chaves `best_baseline_crps`, `best_baseline_pai1`, `best_crossdomain_crps`, `best_crossdomain_pai1`, `laya_ft`, `lightgbm_compressed_state` e `markov_fate_baseline`, escolhidas só com 2025.
2. Rode `cityomics freeze check`: lista o que falta (árvore limpa, testes, cofre nunca aberto, entradas, núcleo de covariáveis, seleção, modelos).
3. Rode `cityomics freeze commit --confirm`: grava `FREEZE_MANIFEST.json`, faz o commit de congelamento e grava `UNSEAL_KEY` com `FREEZE-<sha>`.
4. O cofre só abre se o commit da chave contiver o manifesto completo e `CITYOMICS_UNSEAL_KEY` repetir a chave.

## Como registrar (etapa final)

1. Preencha os campos `[fill in]` de `preregistration.md`: autores, afiliação e parecer ou dispensa do comitê de ética.
2. No OSF, crie um projeto e escolha **Registrations → "Preregistration for secondary data analysis"**. A opção "OSF Preregistration" também serve. Copie as seções.
3. **Embargo:** o OSF permite manter o registro privado por até 4 anos, com a data registrada. Use isso se quiser que o desenho só se torne público junto com os artigos.
4. Depois de aprovado, acrescente o DOI (formato `10.17605/OSF.IO/XXXXX`) ao histórico de `UNSEAL_KEY` e faça um commit.
5. Junto com o registro, anexe `AMENDMENTS.md` e `data/sealed_2026/ACCESS_LOG.jsonl`, que documentam quando o cofre foi aberto.

## Reproduzir a análise de poder

```bash
python prereg/analysis/extract_letal.py ../MapaSegurancaSP/data/raw /tmp/letal_dp_trimestre.parquet
```

```bash
python prereg/analysis/power_letal.py /tmp/letal_dp_trimestre.parquet
```

O primeiro script lê só os arquivos de 2022–2025 e grava contagens agregadas por DP × trimestre, sem número de BO nem endereço.
