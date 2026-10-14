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

## Violência letal (distrito × trimestre)

Arquivo `data/processed/alvos/letal_distrito_trimestre.parquet`. São 1.170 a 1.313 eventos compostos por ano atribuídos a distrito (565 a 611 no CVLI estrito), média de 3,2 por célula.

## Pendências da F2

- **Lotes fiscais e IPTU/TPCL:** só disponíveis pela interface do GeoSampa (sem WFS nem link direto). O WFS tem `quadra_fiscal`, que permite localizar o lote pelo código SQL (setor + quadra) quando houver o cadastro.
- **Estações de metrô e trem** (camadas `estacao_metro` e `estacao_trem` do WFS): vão restringir a distribuição do estrato de trilhos aos setores com estação.
- **Novo geocoding** pelo CNEFE dos registros com logradouro e sem coordenada.
- **Grade estatística de 200 m** (ponte 2010 ↔ 2022, F3).
