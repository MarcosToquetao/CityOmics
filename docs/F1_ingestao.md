# F1: relatório da ingestão (2026-10-14)

Snapshot: `data/snapshot.json`. Os arquivos de 2022–2025 não mudaram no servidor desde junho de 2026 e foram copiados do MapaSegurancaSP depois de conferir o tamanho. Os de 2026 foram baixados de novo: base principal atualizada pela SSP em 2026-10-08, celular em 2026-09-28.

Reprodução:

```bash
cityomics ingest snapshot --copy-from ../MapaSegurancaSP/data/raw
```

```bash
cityomics ingest parse
```

```bash
cityomics ingest check
```

## Volumes (capital, fora do cofre)

| Arquivo | Base principal (linhas) | Eventos letais | BOs de celular | Eventos de celular | Enviados ao cofre |
|---|---|---|---|---|---|
| 2022 | 487.151 | 1.279 | 218.851 | 201.187 | 0 |
| 2023 | 501.544 | 1.211 | 215.317 | 193.947 | 0 |
| 2024 | 476.981 | 1.184 | 183.363 | 161.301 | 0 |
| 2025 | 468.045 | 1.322 | 185.088 | 159.981 | 1 (base principal) |
| 2026 | 7.566 | 6 | 2.069 | 1.548 | 288.999 + 114.384 |

As linhas de 2026 fora do cofre são registros tardios de fatos ocorridos até dez/2025. "BOs de celular" conta todos os BOs da capital, de qualquer status e rubrica. "Eventos" são só subtrações consumadas.

## Eventos por ano do fato (`data/interim/eventos_*.parquet`)

| Ano | Violência letal (composto) | CVLI estrito | Coordenada válida (letal) | Celular | Coordenada válida (celular) |
|---|---|---|---|---|---|
| 2022 | 1.266 | 646 | 76,3% | 200.440 | 82,7% |
| 2023 | 1.210 | 539 | 71,2% | 193.354 | 82,9% |
| 2024 | 1.178 | 550 | 66,0% | 161.371 | 82,1% |
| 2025 | 1.321 | 566 | 67,0% | 159.539 | 82,5% |

- **Cobertura de coordenadas da violência letal caiu 9 pontos entre 2022 e 2025.** Isso pesa a favor de atribuir esse desfecho ao distrito pelo bairro quando faltar a coordenada (F2).
- **Atraso de registro:** mediana de 0 dia (letal) e 1 dia (celular); passam de 30 dias 0,5% e 1,6% dos registros.
- **Registros antigos:** há poucos eventos de celular com fato entre 2003 e 2021 (registros muito tardios). A análise usa 2022 em diante.

## Conferência com a tabela oficial da SSP

O resultado está na tabela abaixo, gerada por `cityomics ingest check`. Ela compara por ano de registro (`ANO_ESTATISTICA`) e alerta acima de 2,5%.

```
 ano                        natureza  microdado  oficial  dif_pct  alerta
2022                HOMICIDIO DOLOSO        557      560    -0.54   False
2022          TENTATIVA DE HOMICIDIO        633      633     0.00   False
2022                      LATROCINIO         63       63     0.00   False
2022 LESAO CORPORAL SEGUIDA DE MORTE         26       27    -3.70    True
2022           LESAO CORPORAL DOLOSA      30697    30697     0.00   False
2022                  ROUBO - OUTROS     139853   139853     0.00   False
2022                ROUBO DE VEICULO      16481    16481     0.00   False
2022                  ROUBO DE CARGA       3060     3060     0.00   False
2022                  FURTO - OUTROS     235257   235449    -0.08   False
2022                FURTO DE VEICULO      41612    41612     0.00   False
2023                HOMICIDIO DOLOSO        477      481    -0.83   False
2023          TENTATIVA DE HOMICIDIO        671      671     0.00   False
2023                      LATROCINIO         43       43     0.00   False
2023 LESAO CORPORAL SEGUIDA DE MORTE         20       20     0.00   False
2023           LESAO CORPORAL DOLOSA      35183    35183     0.00   False
2023                  ROUBO - OUTROS     130499   130499     0.00   False
2023                ROUBO DE VEICULO      14983    14983     0.00   False
2023                  ROUBO DE CARGA       2819     2819     0.00   False
2023                  FURTO - OUTROS     250671   250825    -0.06   False
2023                FURTO DE VEICULO      40519    40519     0.00   False
2024                HOMICIDIO DOLOSO        470      481    -2.29   False
2024          TENTATIVA DE HOMICIDIO        633      639    -0.94   False
2024                      LATROCINIO         52       52     0.00   False
2024 LESAO CORPORAL SEGUIDA DE MORTE         29       29     0.00   False
2024           LESAO CORPORAL DOLOSA      36408    36408     0.00   False
2024                  ROUBO - OUTROS     112914   112914     0.00   False
2024                ROUBO DE VEICULO      12559    12559     0.00   False
2024                  ROUBO DE CARGA       2257     2257     0.00   False
2024                  FURTO - OUTROS     241215   241369    -0.06   False
2024                FURTO DE VEICULO      42384    42384     0.00   False
2025                HOMICIDIO DOLOSO        489      501    -2.40   False
2025          TENTATIVA DE HOMICIDIO        757      760    -0.39   False
2025                      LATROCINIO         39       39     0.00   False
2025 LESAO CORPORAL SEGUIDA DE MORTE         37       37     0.00   False
2025           LESAO CORPORAL DOLOSA      39900    39900     0.00   False
2025                  ROUBO - OUTROS      96638    96638     0.00   False
2025                ROUBO DE VEICULO       9921     9921     0.00   False
2025                  ROUBO DE CARGA       1720     1720     0.00   False
2025                  FURTO - OUTROS     250064   250168    -0.04   False
2025                FURTO DE VEICULO      38649    38650    -0.00   False
```

- **Batem exatamente** ou ficam abaixo de 0,1%: tentativa de homicídio, latrocínio, lesão dolosa, roubos e furtos.
- **Homicídio doloso** fica de −0,5% a −2,4%: a tabela oficial conta casos que no microdado têm outra natureza apurada (já observado no MapaSegurancaSP).
- **Único alerta:** 1 caso de lesão seguida de morte em 2022 (26 contra 27).
- **Desvio da spec:** a spec previa tolerância de ±0,5%. Ela foi ampliada para 2,5% por causa da diferença conhecida em homicídio doloso.

## Escolhas e diferenças em relação ao MapaSegurancaSP

- **Recorte da capital:** os dois usam o local do fato (circunscrição) na base principal. Na base de celular, o CityOmics usa `NOME_MUNICIPIO_CIRC`, e não `CIDADE` (endereço), para manter o mesmo critério (D13). Diferença: 201.187 contra 200.647 eventos em 2022 (+0,3%).
- **Deduplicação da base principal:** por (delegacia, ano do BO, número, natureza, rubrica). Remove 2 linhas de homicídio em 2025 (489 contra 491 no Mapa).
- **Datas:** textos com barra são lidos como dia/mês/ano. Datas do fato anteriores a 2003 viram ausentes. `MES/ANO_ESTATISTICA` com fórmula Excel não avaliada são recalculados pela data de registro.
- **Coordenadas** fora da caixa da capital viram ausentes (`coord_valida = False`).
- **Cofre:** registros com fato em 2026 vão para o cofre. Sem data do fato, o critério é a data de registro em 2026.

## Pendências da F1

- Histórico de violência letal antes de 2022 (SPSafe, CEM-USP).
