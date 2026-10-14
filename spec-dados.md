# Spec — Dados, unidades e covariáveis (F1–F3)

> Parte de [spec-overview.md](spec-overview.md). Esta spec é a base das outras duas: sem F1–F3 não há benchmark nem atlas.

**Em resumo:** ingerimos os microdados de BO da SSP com regras próprias de deduplicação e de data de disponibilidade (as-of). Montamos a hierarquia lote → setor → distrito e reconciliamos a mudança de geocodificação de 2026. Por fim, construímos cerca de 150–300 covariáveis T1+T2 alinhadas no tempo sem vazamento.

## 1. Fontes de crime

| Fonte | Cobertura | Uso |
|---|---|---|
| SSP `SPDadosCriminais_{ANO}.xlsx` | 2022–2026 (estado inteiro; 1 linha por BO × natureza) | Violência letal, tipo de local, contexto |
| SSP `CelularesSubtraidos_{ANO}.xlsx` | 2022–2026 (1 linha por objeto × BO) | Desfecho celular (deduplicado por BO) |
| SPSafe (doi:10.5753/dsw.2023.233945) | 2003–2022 | Histórico de violência letal (D15) |
| CEM-USP | DP × mês, 2000–2020 + polígonos de DP | Histórico de violência letal e checagem |
| SSP API `v1/OcorrenciasMensais/RecuperaDadosMensaisAgrupados` | Totais mensais oficiais | Teste de consistência |

**Fora do escopo:** `ViolenciaDomestica_Base.xlsx` (D14).

### 1.1 Regras de ingestão (`cityomics.ingest`)

- **Snapshot:**
  - Baixar de novo 2025 e 2026 (para incluir ago–set/2026 e as revisões).
  - Copiar 2022–2024 do MapaSegurancaSP (somente leitura).
  - Gravar `snapshot.json` com URL, data de download e sha256 de cada arquivo (D18).
- **Harmonização de schema:**
  - 2022 usa `CIDADE`, `DATA_COMUNICACAO_BO` e `DESCR_PERIODO`.
  - 2023 em diante usa `NOME_MUNICIPIO`, `DATA_REGISTRO` e `DESC_PERIODO`.
  - Em 2026, os nomes de colunas `…CIRCUNCRIÇÃO` viram `…CIRCUNSCRICAO`.
  - Normalizar maiúsculas e espaços e unificar grafias de natureza (TRAFICO/TRÁFICO, "–" e "-").
  - Fórmulas Excel não avaliadas (`=MONTH(...)`) são recalculadas a partir da data de registro.
- **Chave de BO:**
  - Base principal: `(NOME_DELEGACIA, ANO_BO, NUM_BO)`.
  - Base de celular: `(ID_DELEGACIA, ANO_BO, NUM_BO)`, mantendo a maior `VERSAO`.
  - Rubricas que não são subtração (p. ex., "Perda/Extravio") são descartadas.
- **Filtro espacial:** `NOME_MUNICIPIO_CIRCUNSCRICAO == 'S.PAULO'` (local do fato).
- **Datas:**
  - Data do fato = `DATA_OCORRENCIA_BO`; datas anteriores a 2003 ou inválidas viram NA.
  - Data de disponibilidade = `DATA_REGISTRO`.
  - **Regra as-of:** um registro só pode alimentar uma feature de um mês m se tiver sido registrado antes do início de m.
- **Desfechos:**
  - **Celular:** roubo ou furto consumado, na capital, deduplicado por BO. **Não somar** com FURTO/ROUBO-OUTROS (99,7% de sobreposição).
  - **Violência letal (primário, D20):** HOMICÍDIO DOLOSO + TENTATIVA DE HOMICÍDIO + LATROCÍNIO + LESÃO CORPORAL SEGUIDA DE MORTE. Excluir as naturezas "…POR ACIDENTE DE TRÂNSITO".
  - **CVLI estrito (sensibilidade):** o composto sem as tentativas.
- **Cofre de 2026:**
  - Os registros com data do fato em 2026 vão para `data/sealed_2026/`.
  - `cityomics.sealed` recusa a leitura sem as duas chaves: `prereg/UNSEAL_KEY` (DOI do OSF ou `FREEZE-<sha>` do commit de congelamento) e a variável `CITYOMICS_UNSEAL_KEY` com o mesmo valor (D10, D33).
  - **Exceção:** os lags de 2026 usados no protocolo de entradas atualizadas (D25) só podem ser lidos na fase F7.
  - Alvos de 2026 derivados de covariáveis (tipos de lote em 2026-S1, usados no destino celular) também só são calculados depois da abertura do cofre (pré-registro §3).

### 1.2 Fatos conhecidos (auditoria do MapaSegurancaSP @ `6072082`)

- Na capital há cerca de 470 mil registros por ano (BO × natureza) e cerca de 160 mil BOs de celular por ano. Em 2025, a violência letal somou 491 homicídios dolosos, 760 tentativas, 39 latrocínios e 37 lesões seguidas de morte.
- Coordenadas existem em ~80% dos registros (2022–25) e em ~90% a partir de mai/2026. Há **supressão legal por tipo de local**: residência, escola, estacionamento e crimes sexuais. Terminal/Estação tem só 29,5% com coordenadas.
- 37% dos registros são feitos mais de 1 dia após o fato. O último mês, contado pela data do fato, fica subcontado em ~10%.
- Não há campo de precisão da geocodificação. As 1.000 coordenadas mais repetidas concentram 11,6% dos pontos.

## 2. Unidades (`cityomics.units`) — D13, D22

| Nível | Fonte | Papel |
|---|---|---|
| **Lote fiscal** | GeoSampa `lotes` + IPTU/TPCL (emissões anuais desde 1995) + polígonos FCU 2022 (favelas como pseudo-lotes) | Célula do atlas |
| **Setor censitário 2022** | IBGE, malha com atributos | Spot; unidade do desfecho celular |
| **Distrito (96)** | GeoSampa | Órgão; unidade da violência letal |
| Grade estatística de 200 m (2010/2022) | IBGE | Ponte entre 2010 e 2022 e base de pesos dasimétricos |

- **Atribuição de lote a setor:** pelo centroide. Lotes que cruzam a fronteira de um setor são registrados num relatório de qualidade.
- **Atribuição de ponto (fato):**
  - ponto → setor (point-in-polygon);
  - ponto → lote mais próximo, por distância à testada (usado na validação D29);
  - ponto → distrito.

### 2.1 Reconciliação da geocodificação (`units/reconcile.py`) — D16, D27

1. Contar o total por distrito × mês × estrato de tipo de local (`DESCR_SUBTIPOLOCAL` agrupado em: via pública, transporte/estação, comércio, residência suprimida, outros). Esse total usa **todos** os registros: o distrito vem das coordenadas ou, se não houver, do bairro.
2. **Geocodificar de novo** (CNEFE 2022, depois OSM/Nominatim local) os registros que têm logradouro e número mas não têm coordenadas.
3. Distribuir entre os setores os registros que continuam sem coordenadas, usando a fração do setor **dentro do estrato**, estimada com os geocodificados dos 12 meses anteriores (regra as-of). Os estratos de transporte só recebem registros em setores que contêm estação ou terminal.
4. **Invariante:** a soma dos setores é igual ao total do distrito, por estrato e por mês. Vale como teste unitário.
5. As métricas de ranking (hit rate, PAI) também são reportadas com o alvo sem reconciliação.

## 3. Covariáveis ("genes") — D12, D22

### 3.1 Genes do lote (atributos nativos)

- **IPTU/TPCL (anual, desde 1995):** uso, padrão construtivo, área do terreno e construída, número de pavimentos (verticalização), ano de construção e valores unitários (os campos ainda serão verificados).
- **ITBI (lote, mensal, 2006–2026):** número de transações, preço declarado por m², tempo desde a última transação e preço da última transação carregado adiante.
- **CNPJ (snapshot da Receita, reconstrução mensal):** estabelecimentos **ativos** no endereço por grupo de CNAE (bares, restaurantes, farmácias, comércio, serviços, indústria), além de aberturas e fechamentos.
- **CNEFE 2022:** tipos de endereço no lote (domicílio, ensino, saúde, religioso, outras finalidades).
- **Alvarás (Aprova Digital, 2020+):** usados só como contexto (D31).

### 3.2 Genes do setor

- **Censo 2022 por setor:** universo (população, idade, sexo, raça, domicílios), renda do responsável (liberada em mai/2026), entorno (iluminação, calçada, arborização, pavimentação) e favelas (FCU).
- **Censo 2010** levado para a grade de 200 m, com Δ2010→2022 como feature de trajetória.
- **IPVS** 2000/2010/2022.
- **VIIRS Black Marble Collection 2:** VNP46A3 (mensal) e VNP46A4 (anual), com média por área do setor. Usar C2 em **todos** os anos.
- **Metrô:** entradas diárias por estação (2012–2026) → fluxo potencial por distância de rede.
- **OSM/ohsome:** malha viária (centralidade, densidade de interseções) e histórico de POIs.
- **SP156:** reclamações de desordem por trimestre (2015+; semestral em 2012–14): iluminação, entulho, veículos abandonados.
- **BCB:** agências e caixas eletrônicos (mensal).
- **Composição de tipos de lote** no setor (vem do atlas; entra no benchmark só com tipos ajustados até 2025).
- **Contexto de tempo:** INMET A701/CGE (chuva, temperatura) e calendário (feriados, dias de pagamento, Carnaval, jogos em casa, grandes eventos).

### 3.3 Alinhamento temporal (`covariates/asof.py`)

- **Cada fonte tem uma defasagem de publicação** em meses: ITBI e CNPJ, 1; SP156, 3; IPTU, emissão do ano corrente; Censo 2022, desde a data de liberação (com nota de que é análise retrospectiva).
- **Janelas** de 3, 6 e 12 meses, variação ano a ano e lags.
- **Variáveis decenais:**
  - 2010–2022: interpolação log-linear por célula da grade.
  - Depois de 2022: valor de 2022 fixo.
  - População anual: atualização dasimétrica com unidades residenciais do IPTU e pontos do CNEFE.
- **Não temos dados abertos para:** histórico de troca para LED, locais das câmeras do Smart Sampa, microdados da OD 2023. Tratados como limitação.

## 4. Privacidade e armazenamento (D14, D28, D30)

```
data/raw/          microdados (NUM_BO, logradouro, coords) — só local
data/interim/      tabelas com IDs internos; pontos só se necessários
data/processed/    agregados por lote/setor/distrito — podem ir ao Colab
data/sealed_2026/  cofre
```

- O teste `tests/test_privacy.py` varre o repositório e `data/processed/` em busca de colunas proibidas (`NUM_BO`, `LOGRADOURO`, `NUMERO_LOGRADOURO`, `LATITUDE`, `LONGITUDE`) e de padrões de chave de API.
- **Retenção:** `data/raw` é apagado em publicação + 5 anos. A data fica registrada no README.

## 5. Testes de aceitação

- O total mensal da capital por natureza bate com a API da SSP, com tolerância de ±0,5%.
- Nenhum BO duplicado depois da deduplicação, nas duas bases.
- A invariante de reconciliação (§2.1) vale para todo distrito × mês × estrato.
- Teste da regra as-of: feature(m) não muda se removermos todos os registros com `DATA_REGISTRO ≥ início de m`.
- O teste de privacidade passa.

## Decisions Log

| ID | Topic | Decision | Rationale | Source | Date |
|---|---|---|---|---|---|
| D13 | Unidades | Lote → setor 2022 → distrito | Unidades orgânicas | Interview | 2026-10-14 |
| D14 | Privacidade | Excluir violência doméstica; microdados só locais; retenção até publicação + 5 anos | LGPD | Interview | 2026-10-14 |
| D15 | Histórico | Pré-2022 só para violência letal (SPSafe, CEM) | Esparsidade | Interview | 2026-10-14 |
| D16 | Geocodificação | Reconciliação hierárquica | Cobertura de 80% para 90% | Interview | 2026-10-14 |
| D18 | Ingestão | Ingestão própria + snapshot sha256 | Parquets do Mapa sem NOME_DELEGACIA | Interview | 2026-10-14 |
| D20 | Violência letal | Composto primário; CVLI estrito como sensibilidade | Poder estatístico | Red Team | 2026-10-14 |
| D22 | Genes por escala | Lote nativo; setor com Censo etc. | Tipos não colapsam em setores | Red Team | 2026-10-14 |
| D27 | Reconciliação | Estratificada por tipo de local + novo geocoding | Estações sub-geocodificadas | Red Team | 2026-10-14 |

## Dependency Graph & Implementation Order

```
ingest/snapshot ─► ingest/ssp + ingest/celulares ─► sealed
        └─► ingest/spsafe + ingest/cem
units/setores, units/distritos ─► units/lotes (IPTU+FCU) ─► units/assign ─► units/reconcile
covariates/* (independentes entre si) ─► covariates/asof ─► features (spec-benchmark)
```

1. `snapshot` → `ssp`/`celulares` → `sealed` (cofre ativo antes de qualquer análise).
2. `setores`/`distritos` → `assign` (ponto → setor/distrito) → `reconcile`.
3. `lotes` (IPTU + FCU) → `assign` (ponto → lote).
4. Covariáveis T1 → T2 → `asof`.
