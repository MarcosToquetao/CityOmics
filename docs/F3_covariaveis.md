# F3: covariáveis

## Censo 2022 por setor (`covariates/censo.py`)

- **Fonte:** agregados por setor do IBGE, arquivos nacionais filtrados para a capital. Temas: básico, demografia, cor ou raça, alfabetização, domicílio (partes 1 a 3), renda do responsável (liberada em 2026-05-08) e entorno (faces de quadra, domicílios e moradores). Os dicionários oficiais ficam em `data/external/ibge/censo2022/dicionarios/`.
- **Saída:** `data/processed/covariaveis/setor_censo2022.parquet`, com 27.301 setores e 42 indicadores:
  - população, domicílios e densidades;
  - idade e sexo (homens de 15 a 29 anos, 15 a 24, 0 a 14, 60 ou mais, razão de sexo);
  - cor ou raça (branca, preta, parda, negra, amarela);
  - analfabetismo a partir de 15 anos;
  - tipo de domicílio (apartamento, casa, vila ou condomínio, cortiço, estrutura degradada, improvisados);
  - saneamento (água, esgoto, lixo, banheiro, três ou mais banheiros);
  - renda do responsável (média, mediana, coeficiente de variação);
  - entorno, por fração de faces de quadra com: iluminação pública, pavimentação, calçada, obstáculo na calçada, rampa, bueiro, ponto de ônibus, três ou mais árvores, circulação de ônibus e caminhão, circulação só de pedestres.
- **Supressão:** o IBGE suprime células pequenas ("X"). Quando o setor tem total de moradores publicado, uma contagem suprimida vira 0. Isso não vale para médias e variâncias. Setores sem moradores publicados (622, ou 2,3%) ficam ausentes.
- **Tempo:** variável estática de 2022. A renda só foi liberada em maio de 2026, o que é aceitável numa análise retrospectiva (spec-dados §3.3).

## ITBI: transações imobiliárias (`covariates/itbi.py`)

- **Fonte:** Secretaria da Fazenda, "Guias de ITBI pagas", 21 arquivos anuais de 2006 a set/2026, com abas mensais.
- **Volume:** 2.715.199 transações desde 2006. Cada uma traz SQL, natureza, valor declarado, data, valor venal de referência, financiamento, áreas, uso e padrão.
- **Ligação com o lote:** o SQL de unidade de condomínio é levado ao lote pelo IPTU do mesmo ano, do seguinte (lançamentos) e do anterior. 88,2% das transações caem num lote existente hoje; 99,9% chegam a um setor 2022, pelo lote ou pela quadra fiscal (setor da maioria dos lotes da quadra).
- **Lotes extintos:** transações em lotes que depois somem do cadastro são um sinal de incorporação (compra de casas vizinhas → unificação → prédio). A fração por setor e mês fica em `frac_lote_extinto`.
- **Saídas:** `data/interim/itbi/itbi_lote_mes.parquet` (1,25 milhão de linhas lote × mês) e `itbi_setor_mes.parquet` (1,12 milhão de linhas setor × mês). As medidas são número de transações, valor total, mediana do preço por m² e fração financiada.

| Ano | Transações | Preço/m² mediano (R$) | Fração financiada |
|---|---|---|---|
| 2006 | 112.399 | 758 | 18,5% |
| 2010 | 128.360 | 1.288 | 26,6% |
| 2014 | 100.847 | 2.435 | 25,6% |
| 2018 | 89.797 | 2.974 | 21,3% |
| 2021 | 171.003 | 3.000 | 39,6% |
| 2023 | 172.242 | 2.445 | 41,0% |
| 2025 | 229.510 | 2.287 | 43,2% |
| 2026 (jan–set) | 150.986 | 2.302 | 50,5% |

**Cuidado:** a queda do preço mediano por m² a partir de 2022 coincide com o aumento das compras financiadas. Provavelmente é efeito de composição (mais imóveis pequenos financiados), e não queda real de preços. Nos modelos, convém usar preços relativos ao setor ou ao tipo de imóvel.

## Infraestrutura e equipamentos (`covariates/infra.py`)

- **Fonte:** WFS do GeoSampa. Todas as camadas são fotografias atuais (2026), sem histórico. Camadas grandes são baixadas em páginas de 30 mil feições.
- **Saída:** `data/processed/covariaveis/setor_infra.parquet`, com 18 colunas por setor:
  - distância a estação de metrô, estação de trem (e a menor das duas), terminal e corredor de ônibus, delegacia (pontos), base da PM e da GCM, favela, cortiço, parque, praça, UBS e feira livre;
  - contagem e densidade por km² de pontos de ônibus (22.437) e de pontos de iluminação pública (662.095).
- **Iluminação:** todos os pontos já são LED (carga única de 2026-07-14), então só a densidade varia entre setores. Não há histórico de troca para LED (lacuna já prevista).
- **Endogeneidade:** delegacias e bases da PM e da GCM são instaladas onde há crime. Entram como contexto e ficam marcadas para análise de sensibilidade.
- **Áreas de DP:** a camada `delegacia_policia_civil` são polígonos das áreas de DP, não pontos. Ela não é usada aqui, mas serve para cruzar com a delegacia de circunscrição dos BOs.

## Lacunas registradas

- **Demanda do Metrô:** a fonte pública cobre só as linhas 1, 2, 3 e 15. Faltam a Linha 4, a Linha 5 e a CPTM, e as médias mensais por estação só existem para alguns anos. Um fluxo calculado só com essa parte seria enviesado. Fica para depois, quando houver as linhas privadas e a CPTM.

## OpenStreetMap (`covariates/osm.py`)

- **Malha viária:** OSMnx, `network_type="drive"`, simplificada. São 122.550 nós e 304.081 arestas. Por setor: número de nós e interseções, fração de becos sem saída, grau médio, centralidade de intermediação média e máxima (amostra de 1.000 origens, ponderada pelo comprimento, semente fixa), km de vias e densidades. O cálculo leva cerca de 15 minutos.
  - **Setores sem nó (5.793, os pequenos dentro de quarteirões):** a centralidade fica ausente. Na F5, será preenchida pelo nó mais próximo ou pela média dos vizinhos.
- **Pontos de interesse (fotografia de 2026-10-15):** os três servidores Overpass recusaram consultas do tamanho da cidade. A extração foi feita do arquivo da Geofabrik (`sudeste-latest.osm.pbf`, 861 MB) com DuckDB `ST_ReadOSM`: nós com as tags de interesse e vias (prédios, parques) pelo centroide dos seus nós.
  - **Volume:** 35.455 pontos no município, sendo 12.374 lojas, cerca de 1.000 bares e pubs, 974 bancos e 1.511 escolas.
  - **Por setor:** contagem e densidade por categoria (bar e vida noturna, alimentação, banco e caixa eletrônico, farmácia, posto, educação, religioso, saúde, lazer e cultura, comércio, hospedagem, esporte e parque) e distância ao bar mais próximo.
- **Saída:** `data/processed/covariaveis/setor_osm.parquet`, com 35 colunas.
- **Sem série temporal de pontos de interesse:** o histórico do OSM (ohsome) não é usado, porque no Brasil a contagem de pontos cresce sobretudo com o esforço de mapeamento, não com a abertura de estabelecimentos. A série longitudinal de comércio virá do CNPJ.
- Dados © colaboradores do OpenStreetMap (ODbL).

## IPVS 2022 (`covariates/ipvs.py`)

- **Fonte:** base cartográfica do IPVS 2022 da Fundação Seade (grupos 1 a 6, de baixíssima a muito alta vulnerabilidade), por setor do Censo 2022.
- **Saída:** `setor_ipvs.parquet` com `ipvs_codigo`, `ipvs_grupo` e `ipvs_alta` (grupos 5 e 6). São 27.301 setores, 25.875 classificados; os 1.426 "não classificados" (0,6% da população) ficam ausentes.
- **Redundância:** o índice vem do mesmo Censo 2022 (renda, escolaridade, estrutura etária). Vale como resumo composto e referência clássica, mas não traz informação independente da renda e do analfabetismo de `censo.py`. Variável estática.

## Clima e calendário (`covariates/clima.py`, `covariates/calendario.py`)

- **Clima:** reanálise ERA5 pela API de arquivo do Open-Meteo, para um ponto central da cidade, de 2015 a 2026-09-30 (4.291 dias). Temperatura, chuva, vento e radiação, em dia e em mês (dias de chuva forte, dias muito quentes, dias frios). É série da cidade inteira, não por setor.
  - **Chuva subestimada:** a média anual da reanálise (1.233 mm) fica abaixo da normal da estação (cerca de 1.450 mm). Serve para variação no tempo, não para nível absoluto.
- **Calendário:** calculado por regra, 2015 a 2027. Feriados nacionais, estaduais e municipais, Carnaval, Sexta-feira Santa, Corpus Christi, 5º dia útil, dia 20 e 13º salário. Jogos de clubes e blocos de rua ficam de fora, por falta de fonte aberta completa.

## SP156 (`covariates/sp156.py`)

- **Fonte:** 47 arquivos trimestrais e semestrais de pedidos dos cidadãos (2015 a 2026-T3), 3,8 GB no total, do portal de dados abertos da Prefeitura. Anos de 2012 a 2014 ficam de fora. O processamento descarta logradouro, número, CEP e texto livre.
- **Grupos de assunto:** regex sobre tema, assunto e serviço: iluminação, limpeza e entulho, veículo abandonado, árvore e poda, calçada e via, comércio irregular e ruído, imóvel abandonado, população em situação de rua e "outros".
- **Saídas:** `pedidos_<período>.parquet` (um protocolo por linha, sem endereço), `sp156_setor_mes.parquet` (setor 2022 × mês × grupo, 4,37 milhões de linhas, 26.991 setores) e `sp156_cobertura_mes.parquet` (pedidos datados e com coordenada por mês).
- **Cobertura de coordenadas varia no tempo:** cerca de 95% até 2019, 10 a 50% entre 2020-T2 e 2021, e 43 a 63% desde 2022. Os arquivos de 2020-T4 e 2021-T1 misturam layouts de colunas; as linhas fora do layout principal não têm data legível nem coordenada e saem da agregação. Por isso a contagem por setor muda de nível com a cobertura. Na F5, as contagens entram **normalizadas pela cobertura do mês** (coluna `cobertura_coord`) ou só a partir de 2022, quando a cobertura é estável.
- **Datas após o corte:** cerca de 27 mil pedidos têm data entre out e dez/2026, posterior ao snapshot; são tratados como erro de data e removidos.
- **Viés de denúncia:** bairros com mais renda e conectividade registram mais pedidos. SP156 é covariável e contexto, não medida direta de desordem.

## CNEFE e geocodificador (`geocode.py`)

- **Fonte:** CNEFE do Censo 2022, arquivo do município de São Paulo (IBGE, 186 MB). São 5.689.391 endereços com coordenada e código de setor 2022. O código de setor do CNEFE traz o sufixo `P`/`N`; ele é removido para casar com a nossa malha (97,0% dos endereços caem em setores da malha; o resto está em setores fora da malha usada).
- **Níveis:** `numero` (CEP + número), `logradouro` (nome normalizado + número, com abreviações como AV, R, PCA expandidas) e `cep` (centroide dos pontos do CEP). A saída marca o nível para o chamador descartar os grossos.
- **Privacidade:** roda local; nenhum endereço sai da máquina. Saída intermediária em `data/interim/geocode/` (fora do git).

## BCB: agências bancárias (`covariates/bcb.py`)

- **Fonte:** serviço Olinda `Informes_Agencias` do BCB, posição de 14/10/2026: 1.297 agências no município, com endereço, CEP e data de início.
- **Geocodificação:** 807 por número ou logradouro, 390 só por CEP e 100 sem CEP utilizável. O estoque usa só as 807 de nível fino. Os 390 de nível CEP ficam em `agencias_sp.parquet` com a marca para sensibilidade. A cobertura de 62% é uma lacuna conhecida.
- **Viés de sobrevivência:** só agências em funcionamento aparecem; as fechadas somem. O estoque mensal (`setor_bcb_mes.parquet`, 2015-01 a 2026-09) **subestima o passado** e serve como contexto, não como série comparável no tempo.
- **Caixas eletrônicos:** não há base aberta com endereço; ficam de fora. O OSM tem 974 bancos e caixas (`setor_osm.parquet`).

## Painel as-of (`covariates/asof.py`)

- **Regra:** a previsão do mês `m` é feita no início de `m`. Uma fonte com defasagem de `L` meses só entrega o mês `s` na linha `m` se `s + L < m`. Na prática, cada série é deslocada `1 + L` meses para frente antes de qualquer janela, de modo que somas e médias móveis só enxergam o passado disponível. O calendário é determinístico e entra sem deslocamento.
- **Defasagens:** ITBI e CNPJ, 1; SP156, 3; BCB e clima, 0.
- **Derivadas:** somas de 3, 6 e 12 meses para contagens e fluxos (SP156 por grupo, transações ITBI, entradas e saídas do CNPJ), médias de 3, 6 e 12 meses para preço por m² e fração financiada, variação em 12 meses para estoques (agências, estabelecimentos). Ausência de registro vale zero em contagens; estoques herdam o último valor.
- **SP156:** as contagens são divididas pela cobertura de coordenadas do mês (`cobertura_coord`), para a mudança de cobertura de 2020 a 2022 não parecer mudança de desordem.
- **Saída:** `painel_setor_mes.parquet`, de 2015-01 a 2027-03 (cobre a janela prospectiva), com todos os setores e as covariáveis estáticas (Censo, IPVS, infraestrutura, OSM) com prefixo.
- **Testes:** o deslocamento move o mês na quantidade certa; mudar o valor de um mês ainda não publicado não altera a linha de `m` (inclusive nas janelas); janelas só olham para trás.
- **Fora do painel por enquanto:** IPTU/tipos de lote (F6, emissão do ano corrente), VIIRS (falta o token Earthdata), Censo 2010 e população dasimétrica, Metrô.
