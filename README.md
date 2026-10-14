# CityOmics

Predição espaço-temporal de crimes em São Paulo com métodos emprestados de outras ciências, e um atlas da cidade construído com o vocabulário da transcriptômica espacial.

- **Etapa 1 (artigo de data science):** benchmark pré-registrado de métodos da sismologia, epidemiologia, ecologia, astronomia e econometria contra baselines fortes. O Laya entra como camada de decisão calibrada. Treino até 2025; validação em 2026; confirmação prospectiva de nov/2026 a mar/2027.
- **Etapa 2 (artigo de ciências urbanas):** lotes como células, setores censitários como spots, distritos como órgãos. Tipos de lote, atribuição de crime por tipo, nichos, domínios e destino celular semestral.

O desenho completo e as 32 decisões estão em [spec-overview.md](spec-overview.md), com as sub-specs [dados](spec-dados.md), [benchmark](spec-benchmark.md) e [atlas](spec-atlas.md). O pré-registro está em [prereg/](prereg/).

## Ambiente

```bash
mamba env create -f environment.yml
```

```bash
conda activate cityomics
```

```bash
mamba env create -f environment-r.yml
```

```bash
mamba run -n cityomics-r Rscript R/install.R
```

Versões exatas: `conda-linux-64.lock` (Python, conda) e `requirements-pip.lock` (pacotes via pip). Para recriar idêntico: `mamba create -n cityomics --file conda-linux-64.lock` e depois `pip install -r requirements-pip.lock && pip install -e .`

```bash
pytest
```

```bash
cityomics info
```

## Estrutura

```
src/cityomics/   pacote (ingest, units, covariates, features, models, laya, atlas, eval)
  sealed.py      cofre dos dados de 2026
  privacy.py     varredura de segredos e colunas identificadoras
R/               scripts R (INLA, spdep, scoringRules), trocando Parquet com o Python
notebooks/colab/ notebooks finos para GPU (só dados agregados e anônimos)
prereg/          pré-registro OSF e registro de emendas
data/            fora do git: raw/, interim/, processed/, sealed_2026/
```

## Dados e privacidade

- Os microdados de boletins de ocorrência (número do BO, logradouro, coordenadas) ficam só em `data/raw/`, nesta máquina. Nada disso vai para o git, para o Colab ou para APIs externas.
- Saídas públicas são agregadas por setor ou distrito. A violência letal é publicada como taxa suavizada.
- A base de violência doméstica da SSP não é usada.
- **Retenção:** `data/raw/` será apagado cinco anos depois da publicação do último artigo. Os agregados e o código serão depositados no Zenodo.
- `cityomics privacy-scan` procura chaves no repositório e colunas identificadoras em `data/processed/`. Rode antes de cada upload ao Colab e antes de cada commit.

## Cofre de 2026

Os dados com data do fato em 2026 ficam em `data/sealed_2026/`. A leitura exige duas chaves:

1. `prereg/UNSEAL_KEY`, versionado, com o DOI do OSF ou `FREEZE-<sha>` do commit que congela os modelos (hashes e seleção dos melhores da classe);
2. a variável `CITYOMICS_UNSEAL_KEY` com o mesmo valor.

Cada abertura é registrada em `data/sealed_2026/ACCESS_LOG.jsonl`.
