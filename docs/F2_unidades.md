# F2: unidades, atribuição e reconciliação (2026-10-14)

Reprodução:

```bash
cityomics units build
```

## Unidades

- **Setores censitários 2022:** malha com atributos do IBGE (`SP_setores_CD2022.gpkg`, registrada em `data/external/manifest.json`). A capital tem 27.301 setores, reprojetados para EPSG:31983. Atributos levados: população, domicílios, área, situação e marcação de favela (FCU).
- **Distritos:** os 96 distritos IBGE, dissolvidos a partir dos setores (coincidem com os distritos municipais). A hierarquia setor → distrito vem do próprio código do setor.

## Atribuição dos eventos (2022–2025, fora do cofre)

| Desfecho | Coordenada → setor | Bairro → distrito | Delegacia → distrito | Sem distrito |
|---|---|---|---|---|
| Celular | 82,5% | 15,7% | 1,5% | 0,3% |
| Violência letal | 70,0% | 26,0% | 2,9% | 1,2% |

As tabelas bairro → distrito (1.745 bairros) e delegacia → distrito (69 DPs) usam o distrito mais frequente entre os registros geocodificados de 2022–2025, de todas as naturezas. Só entram bairros e delegacias com pelo menos 5 registros e 60% deles num mesmo distrito.

## Reconciliação estratificada (celular, setor × mês)

| Estrato | Eventos | Com coordenada |
|---|---|---|
| Via pública | 512.719 | 90,4% |
| Outros | 118.292 | 83,2% |
| Trilhos (metrô/trem) | 57.377 | 18,2% |
| Residência | 9.306 | 10,4% |
| Ônibus | 8.623 | 99,5% |
| Comércio | 8.387 | 92,7% |

- **Distribuição:** 17,3% dos eventos foram distribuídos entre os setores do distrito, na proporção dos eventos geocodificados do mesmo estrato nos 12 meses anteriores (suavização α = 1; sem histórico, pela população).
- **Invariante:** a soma dos setores é igual ao total do distrito em todos os distritos × meses (diferença máxima de 0).
- **Alvo** (`data/processed/alvos/celular_setor_mes.parquet`): 1.310.448 células (27.301 setores × 48 meses), média de 0,54 evento por célula, 79% das células zeradas.

**Estações:** o estrato de trilhos só é distribuído entre os 1.578 setores a até 250 m de uma estação de metrô ou trem (94 de metrô e 109 de trem, camadas do WFS do GeoSampa). Esses setores são 5,8% do total e concentram 31,8% do crime de celular reconciliado.

## Violência letal (distrito × trimestre)

Arquivo `data/processed/alvos/letal_distrito_trimestre.parquet`. São 1.170 a 1.313 eventos compostos por ano atribuídos a distrito (565 a 611 no CVLI estrito), média de 3,2 por célula.

## Lotes fiscais (células do atlas)

Reprodução:

```bash
cityomics units lotes --download
```

```bash
cityomics covariates iptu --download
```

- **Fonte:** novo GeoSampa, camada "Lote" (id 352). O download segue as mesmas chamadas da interface (`Download/Nas/Tree` e `Download/Download`; `cityomics.geosampa`). São 96 GeoPackages por distrito, atualizados em 2026-10-11, com 557 MB.
- **Células:** 1.687.685 lotes fiscais e 1.712 favelas do GeoSampa (HABISP, WFS) como pseudo-lotes, que somam 25,3 km². A área mediana do lote é de 175 m². Cada célula recebe o setor 2022 que contém seu ponto representativo; só 0,01% ficou sem setor.
- **Chave:** `sql_base` = setor fiscal (3) + quadra (3) + lote (4). Há 13.580 lotes com código de condomínio 01, 7.387 com 02, e assim por diante.

## Cadastro IPTU/TPCL por lote (1995–2026)

- **Fonte:** download genérico da mesma camada (`IPTU_<ano>.zip`), 32 arquivos com 1,92 GB.
- **Agregação:** uma linha por imóvel tributado (3,9 milhões em 2026), agregada por lote em `data/interim/iptu/iptu_lote_<ano>.parquet`. Imóveis comuns usam a chave do SQL; unidades de condomínio vão para o lote do condomínio (setor + quadra + código do condomínio).
- **Atributos:** número de unidades, áreas, pavimentos, ano de construção, valores do m² e frações de uso (residencial, comércio, serviços, indústria, terreno) e de padrão construtivo (baixo, médio, alto).

| Ano | Imóveis ligados a lote | Lotes atuais com IPTU | Lotes no ano |
|---|---|---|---|
| 1995 | 99,4% | 81,4% | 1.543.074 |
| 2000 | 99,3% | 85,2% | 1.563.425 |
| 2005 | 99,2% | 88,4% | 1.583.370 |
| 2010 | 99,2% | 91,5% | 1.609.574 |
| 2012 | 99,2% | 93,2% | 1.625.777 |
| 2015 | 99,0% | 94,4% | 1.630.244 |
| 2020 | 99,0% | 96,1% | 1.638.984 |
| 2021 | 99,0% | 95,0% | 1.613.686 |
| 2025 | 99,0% | 97,7% | 1.647.826 |
| 2026 | 99,0% | 98,2% | 1.649.545 |

O relatório completo, ano a ano, está em `data/interim/iptu/relatorio_ligacao.json`.

- **Nascimentos e mortes de células:** a cobertura dos lotes atuais cresce com o tempo porque lotes nascem e desaparecem por desmembramento e unificação. Para o destino celular (D23), isso é um evento a modelar, e não uma falha.
- **2021:** o cadastro desse ano tem cerca de 25 mil lotes a menos que 2020 e 2022. É uma peculiaridade da fonte, a tratar como possível quebra.
- **Leitura:** o CSV é lido sem tratamento de aspas, porque há endereços com aspas soltas (2024). Ficam no máximo 6 linhas irregulares por ano, que são truncadas.

## Pendências da F2

- **Novo geocoding** pelo CNEFE dos registros com logradouro e sem coordenada.
- **Grade estatística de 200 m** (ponte 2010 ↔ 2022, F3).
