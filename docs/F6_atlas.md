# F6 — Atlas mínimo do CityOmics (desenvolvimento, 2022–2025)

Specs: [spec-atlas.md](../spec-atlas.md) (emendado), [spec-figuras.md](../spec-figuras.md). Decisões D38–D62. Código em `src/cityomics/atlas/`, saídas em `data/processed/atlas/` (fora do git). Para regerar: `cityomics atlas run`.

**Duas salvaguardas:**
- Nada de 2026 é lido (`atlas/guard.pre2026`).
- Toda análise que usa crime exclui os 19 distritos do cofre espacial (`prereg/atlas_vault.json`, D53). Os números abaixo vêm dos 77 distritos de exploração (21.331 setores).

## 1. Genes do lote (`genes_lote.py`)

- **Células:** 1.651.813 lotes fiscais (a chave `sql_base`; ~17 mil chaves tinham polígonos repetidos e foram unificadas). 1,61 milhão têm IPTU 2025.
- **Testada:** mediana de 7,6 m. É a exposição de cada lote à rua (D51).
- **CNPJ:** snapshot de 2025-12 (D56). São 2,49 milhões de estabelecimentos ativos em SP.
  - **Ligação ao lote:** 73,8% pelo endereço do IPTU (CEP + número → SQL), ou 82% sem contar os MEI. Pelo ponto do CNEFE dentro do lote eram só 31,7%.
  - **MEI:** 957.599 vigentes, contados à parte (D60: nunca saem da máquina).
- **Genes:** 30 no total, sendo 18 do IPTU e 12 do CNPJ (11 grupos de CNAE + MEI).

## 2. Tipos de lote (`typing.py`)

- **Método:** PCA com 15 componentes (90% da variância).
- **Estabilidade sem crime (D53):** Leiden em 8 subamostras de 80 mil lotes por resolução, com rótulos transferidos a 40 mil lotes comuns e comparados por ARI. Alvo de 10 a 16 tipos:

  | Resolução | ARI médio | Tipos (mediana) |
  |---|---|---|
  | 0,02 | **0,973** | 14 |
  | 0,04 | 0,925 | 20 |
  | 0,07 | 0,909 | 23,5 |
  | 0,11 | 0,949 | 27,5 |
  | 0,16 | 0,792 | 31,5 |

- **Referência:** Leiden em r = 0,02 sobre 80 mil lotes estratificados por distrito.
  - 4 tipos minúsculos (< 0,3%) foram fundidos.
  - Transferência kNN para todos os lotes.
- **Sub-agrupamento vertical:** o tipo misto absorveu os prédios (81% dos lotes com ≥ 8 pavimentos). Um sub-agrupamento por regra de genes (≥ 4 pavimentos ou ≥ 8 unidades) separou 10.281 lotes como "vertical residencial e misto", o refinamento usual de um grupo heterogêneo.
- **Baseline:** o k-means no estilo OAC concorda com o Leiden em ARI = 0,71.
- **Os 12 tipos** (nomes por regras sobre o perfil médio, sem crime):

  | Tipo | Lotes |
  |---|---|
  | Residencial horizontal popular | 604.523 |
  | Residencial horizontal médio | 546.677 |
  | Terreno vago | 89.076 |
  | Misto residencial e comercial | 87.687 |
  | Comércio de rua popular | 62.974 |
  | Casa e comércio atacadista | 57.156 |
  | Residencial horizontal alto padrão | 46.626 |
  | Residencial de esquina | 41.890 |
  | Comércio de rua médio | 26.235 |
  | Serviços e equipamentos | 21.916 |
  | Indústria e galpões | 18.399 |
  | Vertical residencial e misto | 10.281 |

- **Favelas:** entram como 3.879 pseudo-células FCU (D54). A exposição é dada em domicílios informais × 7,0 m, a testada por unidade dos lotes populares. Nos mapas, a FCU prevalece sobre o cadastro: em favelas como Paraisópolis, os lotes fiscais aparecem como "terreno vago", porque as casas informais não pagam IPTU.

## 3. Arquitetura (`niches.py`)

- **Vizinhança:** grafo kNN (k = 8) com 13,2 milhões de arestas e 100 permutações restritas a distrito × decil de densidade (D59).
  - A atração mais forte entre tipos diferentes é entre os comércios: atacadista ↔ comércio popular (z = 99), comércio popular ↔ misto (z = 81), comércio médio ↔ popular (z = 78).
  - A maior segregação é entre terreno vago e residencial popular (z = −216).
  - A auto-vizinhança é alta em todos os tipos. Nos lotes de esquina (z = 927) é um efeito geométrico: as quatro esquinas de um cruzamento são vizinhas.
- **Domínios:** composição do setor suavizada no anel de contiguidade e agrupada por k-means. O k = 8 foi escolhido pela silhueta (0,162). Nomes pelos elementos mais enriquecidos:

  | Domínio | Elementos mais enriquecidos |
  |---|---|
  | N1 | vago + arteriais |
  | N2 | popular + vago |
  | N3 | favelas + vago |
  | N4 | vias locais + coletoras |
  | N5 | vertical + arteriais |
  | N6 | popular + esquinas |
  | N7 | comércio médio + alto padrão |
  | N8 | médio + indústria |

## 4. Atribuição do crime às classes de célula (`attribution.py`)

- **Modelo:** y_s ~ Poisson(Σ_k E_sk · λ_k), ajustado por EM, com bootstrap de 500 reamostras por distrito.
- **Celular em 2025:** 121.434 casos nos setores de exploração. A composição sozinha explica D² = 0,34.
- **Taxas por km de frente (lotes) ou de rua, por ano:**

  | Classe | Roubos/km/ano | IC 95% |
  |---|---|---|
  | Comércio de rua médio | 70,5 | 48–96 |
  | Vertical residencial e misto | 36,7 | 19–56 |
  | Comércio de rua popular | 29,8 | 20–44 |
  | Serviços e equipamentos | 26,0 | 17–35 |
  | Misto residencial e comercial | 13,6 | 8–21 |
  | Ruas arteriais | 4,6 | 2,8–6,8 |
  | Ruas coletoras | 2,4 | — |
  | Ruas locais | 1,4 | — |
  | Favelas | 0,5 | — |
  | Residencial horizontal | 0,01–0,14 | — |

  Estações de trilho: 87 roubos por estação por ano. Terminais de ônibus: 71.
- **Validação pontual (D29, D51):** 100.347 eventos geocodificados de 2025, fora do cofre.
  - Destino dos eventos: 4.944 ligados a estações (até 100 m) e 93.483 ligados ao segmento de rua mais próximo, repartidos entre os lotes lindeiros pela testada.
  - Resultado: Spearman entre a taxa atribuída e a observada = **0,93**.
- **Sankey (D47/D57):** λ_k depende de 4 grupos teóricos. A decomposição usa Shapley exato com referência no setor médio, e o efeito de distrito entra como nó "espacial".

## 5. Quanto do "onde" é tecido (`variance.py`)

- A variância entre setores responde por **84%** da variância do celular setor × mês (ICC de 2025, setores de exploração).
- R² fora da amostra (CV por distrito) da taxa de 2025 do setor:

  | Conjunto | R² |
  |---|---|
  | Tipos | 0,22 |
  | Mesmos genes sem tipagem (comparador de H3, D55) | 0,26 |
  | Tecido (tipos + domínios + ruas) | 0,25 |
  | Tecido + covariáveis do setor | 0,31 |
  | Média histórica 2022–2024 | **0,48** |

- **Leitura honesta:** o tecido explica cerca de um terço da geografia do crime sem memória de crime nenhuma, e a tipagem não acrescenta nada sobre os genes brutos. O resto do "onde" é a persistência do próprio lugar (média histórica). Isso afina a D35: o tecido define o mapa de oportunidades, e a história do lugar fixa onde ele de fato se realiza.

## 6. Benchmark por distrito × trimestre (`models/letal_run.py`, D41/D61)

| Desfecho | Melhor modelo (CRPS) | Contra o NB-GLM |
|---|---|---|
| Letal | NB-GLM 1,076 | nenhum modelo melhor (LightGBM 1,120; Hawkes 1,093; BYM-EB 1,085) |
| Celular (pareado) | LightGBM 37,6 | −0,83, com p ajustado de 1,0 (não significativo) |

Na escala do órgão (distrito), os métodos não se separam.

## 7. Destino reduzido: estabilidade do tecido (`fate.py`, D42/D56)

- **Classificador:** LightGBM multiclasse sobre os genes do IPTU. Acerta a família de 2025 em 93,6% dos lotes de teste.
- **Período:** aplicado aos cadastros de 2012 a 2025; os pares de anos com 2021 ficam fora.
- **Permanência média:** 98,2% dos lotes ficam na mesma família de um ano para o outro. É um teto: parte das "transições" vem do erro do classificador.
- **Renovação:** a mediana por setor é de 0,4% dos lotes por ano.
- **Ligação com o "quando":** a correlação entre renovação e variabilidade mensal do crime dentro do setor é fraca, Spearman de 0,13 (4.073 setores com média > 0,5/mês, fora do cofre).
- **Leitura:** o tecido muda devagar, coerente com a previsibilidade do "onde". Os lugares que mudam mais variam um pouco mais.

## 8. Comunicação: multiverso exploratório (`communication.py`, ED2)

| Abordagem | Resultado | Leitura |
|---|---|---|
| L–R criminológico (12 pares, ℓ = 250–1.000 m) | Força estável (ρ de bootstrap = 0,99) e 1.390 pares de tipos com p < 0,05 a 500 m. A atividade no estilo NicheNet não acrescenta previsão: melhor par ônibus → alvos a pé = +0,02%; os demais ficam negativos | A comunicação teórica descreve a co-localização de geradores e alvos, mas não prevê além da história |
| Knox entre famílias (449 mil eventos, 400 m × 1–14 dias) | Razão média de 1,12. As maiores razões ficam dentro de favelas (1,68), terrenos vagos (1,40) e indústria (1,27) | A repetição próxima é mais forte nas bordas informais e vazias do tecido |
| MISTy | R² combinado de 0,33. Contribuições: intrínseca 0,73, justaposta 0,25, para-espacial (1 km) 0,02 | O crime é uma propriedade do próprio spot e da vizinhança imediata, quase nada vem de 1 km |
| NCEM/SLX | As interações tipo × vizinhança pioram a previsão fora da amostra (−5,9%) | Sobreajuste: o efeito de vizinhança é aditivo, não específico por par |
| Lee's L | Todos os ligantes têm associação positiva com o roubo (p = 0,01): vida noturna 0,27, trilhos 0,25, varejo 0,21, ônibus 0,13, dinheiro 0,12 | Os geradores e atratores co-localizam com o crime |
| OD 2017 e ablação do GNN | Não rodados (base OD indisponível localmente; GNN fora desta versão) | Registrados na tabela multiverso |

A escolha do que vai para o corpo do artigo é do autor (D40), via `prereg/A11_DRAFT.md`. A confirmação no cofre espacial só roda depois da emenda.

## 9. Narrativa B: painel de fenótipos (`fenotipo.py`, D63, D64)

- **Eventos:** 15 fenótipos (1,83 milhão de eventos em 2022–2025 na cidade), a partir da base principal da SSP e dos eventos de celular e letal (`data/interim/eventos_multi_atribuidos.parquet`).
  - Os BOs de celular saem de FURTO/ROUBO - OUTROS (chave delegacia × ano × número).
  - Ficam fora: iniciativa policial, estupro e lesão dolosa em residência.
- **Alvos:** reconciliação estratificada por fenótipo, setor × ano (`fenotipo/fenotipo_setor_ano.parquet`).
- **Assinaturas (2024–2025):** EM do Poisson linear para todos os fenótipos de uma vez (`attribution.em_fit_multi`).
  - 11 classes distintas no topo do enriquecimento.
  - Correlação mediana entre os perfis dos fenótipos: 0,58.
  - Controle positivo: o trânsito tem a maior taxa por km nas vias arteriais (1,50 contra 0,62 nas locais).
  - Validação pontual mediana entre tipos de lote: ρ = 0,85, em 12 fenótipos.
- **Programas (NMF):** o menor k ≥ 3 estável entre sementes dá k = 4 (estabilidade 0,96): transporte, centro denso, logística periférica e residencial.

## 10. Relógio do tecido (`fenotipo.relogio`, D65)

| Fenótipo | Resultado |
|---|---|
| Furto de celular | P = 0,005 em 2024 e em 2025 (200 permutações dos períodos dentro do distrito); réplica r = 0,93 |
| Roubo de celular | P = 0,005 em 2024 e 0,07 em 2025; réplica r = 0,90 |
| Residencial horizontal popular | 39% do roubo entre 4 h e 6 h |
| Comércio | pico entre 19 h e 22 h |
| Estações | pico às 18 h |

## 11. População presente (`presenca.py`, OD 2017, D65)

- **Construção:** a partir da OD 2017 (183.092 registros), por setor × hora.
  - Presença: linha do tempo das pessoas pelo FE_PESS. Às 3 h, 12,2 milhões de pessoas no município.
  - Pessoas a pé na rua: minutos andando nas pontas de cada viagem, pelo FE_VIA. São 4,0 milhões de pessoas-hora por dia.
  - Tudo vai para uma grade de 100 m com suavização de 300 m.
- **A ordem das classes sobrevive à multidão:**
  - Spearman entre o ranking por km e o ranking por pedestre: roubo 0,75, furto 0,86;
  - por pessoa presente: 0,84 e 0,90.
- **O relógio não segue os pedestres:**
  - correlação mediana por classe entre o perfil horário do roubo e o dos pedestres: 0,03;
  - risco por pedestre na cidade: máximo às 3 h (19× a média), mínimo ao meio-dia.
- **Ressalva:** a OD é de 2017 e só cobre dias úteis.

## 12. Memória do lugar (`memoria.py`)

- **Variância entre setores do log da taxa anual (2022–2025):**

  | Recorte | Tecido | Memória estável além do tecido | Transitória | Covariância |
  |---|---|---|---|---|
  | Todos os setores | 42% | 48% | 23% | −13% |
  | Setores com ≥ 10 casos esperados por ano | 18% | 58% | — | — |

- **Persistência do resíduo:** 0,70, 0,65 e 0,63 com 1, 2 e 3 anos de defasagem.

## 13. Queda de 2022 a 2025 (`fenotipo.queda`)

- **Celular nos setores de exploração:** −20%, de 151,6 mil para 121,4 mil. É uma queda do roubo (−40%), não do furto (−2%).
- **Com a composição de 2025 fixa:**
  - caíram mais que a cidade: ruas locais (razão relativa 0,76, IC 0,65–0,87) e residencial horizontal popular e de esquina (0,27–0,28);
  - mantiveram a taxa: estações (86 → 87 por estação) e comércio médio (70 → 71 por km);
  - subiram em relação à cidade: estações (1,27) e misto (1,48).
- **Concentração:** as três classes que mais contribuíram para a queda somam 21 pontos acima da participação delas em 2022.

## 14. Limite de previsibilidade (`previsibilidade.py`)

- **No total ("onde e quando"):** o ensemble alcança 87% a 99% do R² máximo sem modelo, em todas as escalas.
- **Dentro do setor (o mês a mês):**
  - R² de 0,018, para um máximo de 0,56;
  - o teste de dispersão por setor mostra que 96% dos setores são compatíveis com ruído de Poisson;
  - o 1% de setores com mais crime concentra 34% do crime e 88% do excesso de variância.

## 15. Perturbação natural (`perturbacao.py`)

- **Desenho:** CNPJ do snapshot de 2025-12 (5,9 milhões de estabelecimentos, inclusive os baixados), dos quais 3,07 milhões ligados a um lote pelo endereço.
- **Seis variantes:** abertura de bar, abertura de varejo e fechamento de bar; cada uma com qualquer CNPJ e com só não-MEI em lote comercial.
- **Resultado:** sem pré-tendência e sem efeito em 12 meses. Efeitos acima de 4–11% da base ficam excluídos.

## 16. Confirmação no cofre (`confirmacao.py`, D68)

- **Família de B:** A-R1, A-R2, A-R6, A-R7 e A-R8, com Holm.
- **Trava:** o código só roda com a A11 datada em `prereg/AMENDMENTS.md`, e uma única vez.
- **Ensaio em pseudo-cofre** (19 distritos de exploração sorteados): todas as cinco sustentadas.

  | Afirmação | Estatística | p de Holm |
  |---|---|---|
  | A-R1 | ρ 0,92 | 0,001 |
  | A-R2 | ρ 0,63 | 0,010 |
  | A-R6 | 0,85 | 0,001 |
  | A-R7 | — | 0,004 |
  | A-R8 | 0,82 | 0,004 |

- **A-R5 (fora da família):** ΔR² = −0,018 (p = 0,89).
