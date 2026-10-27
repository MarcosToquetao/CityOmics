# Narrativa do artigo e análises complementares

> Análise de 2026-10-19, feita a pedido do autor. Pergunta: a história "cidade como tecido" sustenta um artigo, ou o caminho tradicional com muito dado é melhor? Que análises faltam? Os números vêm do desenvolvimento (2022–2025, fora do cofre espacial; ver [F5_benchmark.md](F5_benchmark.md), [F5_laya.md](F5_laya.md) e [F6_atlas.md](F6_atlas.md)). Nada aqui muda decisões fechadas (D1–D62). A escolha da narrativa e qualquer emenda continuam com o autor.

> **Atualização de 2026-10-19 (tarde):** o autor adotou a narrativa B (D63, `spec-figuras.md`). As seções 9 e 10 trazem os resultados de P4 refinado, P5, P6 e P7, o refinamento da tese e o mapa das figuras.

## Em resumo

- **A metáfora sozinha não sustenta.** Onde os métodos de ômica espacial competem em previsão, eles empatam com os análogos urbanos clássicos.
- **O tradicional com muito dado sozinho é incremental.** A concentração do crime em poucos lugares já é lei consolidada.
- **O publicável em alto impacto é a metáfora como instrumento de medida.** Ela vale onde produz uma análise que a caixa de ferramentas urbana não tem, e cada afirmação é testada contra o análogo clássico. Onde não acrescenta, isso vira resultado numa auditoria de equivalências.
- **Narrativa recomendada (B):** o crime é um fenótipo do tecido urbano. A composição do lugar fixa onde, que crime e a que hora acontece; o mês a mês está no limite da previsibilidade.
- B depende de três pilotos baratos com dados já locais: painel multi-crime (P1), relógio do tecido (P2) e decomposição da queda 2022→2025 (P3). Uma perturbação natural (P4) seria o terceiro ato.
- **Os pilotos (seção 8) sustentam B:**
  - **Que crime:** 15 fenótipos têm assinaturas distintas por classe, com validação pontual mediana ρ = 0,85.
  - **A que hora:** na periferia popular, 39% dos roubos de celular acontecem entre 4h e 6h; no comércio, o pico é entre 19h e 22h.
  - **Mudança:** a queda de 20% de 2022 a 2025 veio da malha difusa, e os polos mantiveram a taxa.
  - **Perturbação:** a abertura ou o fechamento de um estabelecimento não move o crime do segmento em 12 meses (nulo, com efeito mínimo detectável de 4–6%). Fica no ED.

## 1. Diagnóstico

### O que é novo e sólido

| Resultado | Número | Por que importa |
|---|---|---|
| Atribuição com composição conhecida, na escala do lote | Comércio de rua médio 70 roubos/km de frente/ano; estação 87/ano; residencial horizontal ≈ 0; validação pontual ρ = 0,93 | A regressão ecológica não separa classes dentro do setor; é a inversa da deconvolução e não tem equivalente urbano |
| O "onde" é estrutural | ICC = 0,84; tecido sem memória de crime R² = 0,25 (0,31 com covariáveis); 98,2% dos lotes ficam na mesma família por ano | O mapa do crime é uma propriedade estável do lugar |
| Limite de previsibilidade | Captura em 5% da área: ensemble 53%, teto de ruído 52%, média histórica 52%, oráculo 65% | O "quando" não é difícil por falta de método: o modelo já está no teto |
| Rigor | Pré-registro, cofre espacial (19 distritos), cofre temporal (2026), janela prospectiva | Raro em ciência urbana; é argumento de venda |

### O que um revisor vai atacar

1. **A tipagem não supera os genes brutos** (R² 0,22 contra 0,26), e os domínios quase não acrescentam (0,25). Se a Fig. 2 for vendida como "tipos que preveem", ela cai.
2. **A comunicação não prevê.** L–R +0,02% no melhor par; NCEM −5,9%; MISTy atribui 73% ao próprio spot. A Fig. 3 é a mais fraca do corpo do artigo.
3. **Memória maior que tecido.** A média histórica (R² 0,48) explica mais que o tecido (0,31). Falta dizer o que é essa memória.
4. **Benchmark lido como negativo.** Ganho de 4% em CRPS, H1b nulo, H2 a favor do LightGBM, em 2 de 6 figuras.
5. **Denominador ausente.** O crime alto em estações e no comércio pode ser só gente demais. A população presente (ambient population) é a crítica mais previsível de criminólogos.
6. **Fenótipo pobre.** Só dois desfechos, enquanto a base da SSP tem ~470 mil registros/ano na capital, com ~20 naturezas e condutas sem uso.

## 2. Metáfora × tradicional

- **Contra a metáfora pura:** um revisor da Nature Cities pergunta o que se aprende sobre cidades que não daria para aprender sem ela. "Ler a cidade como tecido" não responde, e os resultados preditivos mostram empate com os análogos.
- **Contra o tradicional puro:**
  - a lei da concentração do crime é consolidada: mediana de 50% do crime em ~4,5% dos segmentos (Weisburd et al. 2024);
  - concentração e trajetórias por tipo de crime já foram estudadas (Andresen et al. 2017);
  - o efeito do comércio sobre o crime de rua tem estimativa causal (Twinam 2017).
  
  O diferencial (megacidade do Sul Global, lotes, favelas) dá um bom artigo de criminologia, não um de alto impacto.
- **A síntese:** a analogia vale quando gera uma análise nova sobre a cidade. Há quatro casos:

  | Conceito ômico | Análise urbana que ele gera | Já existe? |
  |---|---|---|
  | Spot de composição conhecida | Taxa por classe de célula dentro do setor, validada por ponto | Pronto (Fig. 4) |
  | Segunda modalidade, matriz-assinatura | Assinatura criminal de cada classe (que crime) | P1 |
  | Expressão circadiana específica do tipo celular | Relógio do tecido (a que hora) | P2 |
  | Perturbação in situ | Resposta do tecido a aberturas e fechamentos | P4 |

- Onde a analogia não acrescenta, o artigo diz isso numa tabela (seção 4). **O artigo vende uma descoberta sobre cidades; a analogia é o método.**

## 3. Narrativas candidatas

| # | Tese | Figura-âncora | Revista | Exige ainda | Risco |
|---|---|---|---|---|---|
| A (atual, D35) | Onde é tecido, quando é difícil | Atribuição (Fig. 4) | Nature Cities | Nada | Metade lida como negativa; Fig. 3 fraca |
| **B** | O crime é um fenótipo do tecido: a composição fixa onde, que crime e a que hora; o mês a mês está no limite da previsibilidade | Matriz classe × crime + relógio do tecido | Nature Cities (alt.: Nature Human Behaviour) | P1, P2, P3 (P4 desejável) | Assinaturas ou ritmos pouco nítidos (gates G1, G2) |
| C | Memória do lugar: o tecido desenha as oportunidades, a história decide onde se realizam; perturbações mostram a resposta | Evento-estudo | Nature Cities / PNAS | P4 + P6 | Causal difícil; efeito pequeno; poder |
| D | Concentração na escala do lote numa megacidade do Sul Global + benchmark | Curva de concentração | J Quant Criminol, Env & Planning B, EPJ Data Sci | Pouco | Incremental |
| E | O que a ômica espacial pode e não pode fazer pelas cidades | Auditoria de equivalências | Nature Comput Sci, Patterns, PNAS Nexus | SVG, OD | Mais de métodos que de cidades |

### Rascunhos (EN) de título e primeira frase do resumo

- **A.** *Urban tissue sets where crime occurs but not when.* "We read São Paulo's 1.65 million parcels as cells of a tissue and show that its composition fixes where phone theft concentrates, while month-to-month variation remains largely unpredictable."
- **B.** *Crime is a phenotype of urban tissue.* "Treating a megacity as a spatially resolved tissue, we show that the composition of 1.65 million parcels, streets and stations sets which crimes occur, where and at what hour, and that monthly fluctuations lie at the limit of predictability."
- **C.** *Places remember: tissue and memory in the geography of crime.* "Urban form sets the map of criminal opportunity, but past crime predicts its realization better than form; natural perturbations of the tissue reveal how much of this memory is structural."
- **D.** *Parcel-scale crime concentration in a Global South megacity.* "Using 1.9 million police records and 1.65 million parcels, we measure crime concentration and its land-use correlates at the scale of the lot."
- **E.** *What spatial omics can and cannot tell us about cities.* "We transpose the spatial-transcriptomics toolkit to a megacity and audit, module by module, what it adds over the urban analogue."

### Recomendação: B, com C como terceiro ato se P4 funcionar

B transforma os negativos em descoberta:
- **"Quando" tem duas escalas.** A escala do dia é estruturada pelo tecido (relógio). A escala do mês é ruído em torno de uma taxa fixada pelo lugar, no teto de previsibilidade (no espírito de Song et al. 2010).
- **O ganho de 4% dos métodos emprestados é a distância até o teto**, não uma falha.
- **A tipagem tem papel claro:** classes discretas com exposição são o que permite dizer "70 roubos por km de frente de comércio médio". O papel do tipo é interpretar e atribuir, não prever, e o texto diz isso.

**Arco de figuras (6; benchmark completo e Laya/H2 no ED):**
1. **Anatomia:** a cidade como tecido (Fig. 1 atual).
2. **Tipos e arquitetura:** Fig. 2 + nichos e domínios. A comunicação vai para o ED com o multiverso.
3. **Fenótipo:** matriz classe × crime; programas de crime no mapa; controle positivo (trânsito → arteriais); validação pontual por tipo.
4. **Ritmo:** perfil hora × classe; dia útil × fim de semana; taxa por pessoa presente (se P5).
5. **Estabilidade, memória e mudança:** variância tecido × memória; permanência de 98%; decomposição da queda 2022→2025; evento-estudo (se P4).
6. **Limites e confirmação:** captura × teto × oráculo; forest compacto; celular × letal no órgão; cofre, 2026, prospectiva, equidade.

## 4. Auditoria de equivalências (proposta de ED)

| Módulo | Método ômico | Análogo urbano | Resultado (dev) | Quem vence |
|---|---|---|---|---|
| Tipagem | Leiden em PCA, estabilidade por subamostras (ARI 0,973) | k-means estilo OAC | Concordância ARI 0,71; R² do setor: tipos 0,22 × genes brutos 0,26 | Genes brutos na previsão; tipos na interpretação e na atribuição |
| Atribuição | Poisson de composição conhecida (inversa da deconvolução) | Regressão ecológica por setor | D² = 0,34 só com composição; validação pontual ρ = 0,93 | Ômica (capacidade nova) |
| Nichos | Enriquecimento de vizinhança com nulo restrito | Colocation quotient | Spearman entre os dois = 0,76 (0,71 fora da diagonal) | Empate; o nulo restrito é o ganho |
| Domínios | Composição suavizada + k-means (estilo CellCharter) | Regionalização (SKATER/max-p, não rodado) | R² tecido 0,25 × tipos 0,22 | Ganho marginal |
| Comunicação | L–R criminológico (COMMOT/NicheNet) | Lee's L, lag espacial | L–R +0,02% no melhor par; Lee's L positivo para todos os geradores | Clássico (mais simples, mesma leitura) |
| Contexto | MISTy | Lag espacial | Intrínseco 0,73; justaposto 0,25; para-espacial 0,02 | Empate; MISTy dá a partição |
| Interação | NCEM/SLX com pares | SLX aditivo | Pares pioram 5,9% | Clássico |
| Destino | Classificador de família (IPTU) | Matriz de transição | Permanência 98,2%/ano | Descritivo |
| Previsão | GNN, Hawkes, Chronos, MaxEnt, BYM2, Laya | NB-GLM, média histórica | Melhor: GNN −4% CRPS; Laya-FT perde para LightGBM no mesmo estado | Ganho pequeno e real; no teto |

## 5. Análises complementares

| P | Análise | Análogo ômico | Comparador clássico | Dados | Custo | Figura |
|---|---|---|---|---|---|---|
| **P1** | Painel multi-crime: λ por classe × ~12 fenótipos; programas por NMF; controle positivo | Segunda modalidade (CITE-seq), matriz-assinatura (CIBERSORTx), programas (cNMF) | Concentração por tipo (Andresen 2017), quociente de localização | Local (`data/raw/bo/ssp_*`) | Baixo–médio | 3 |
| **P2** | Relógio do tecido: λ por período do dia, hora e dia da semana; permutação | Expressão circadiana por tipo celular | Uso do solo × sinais temporais; atividades rotineiras | Local (hora exata em 48–58%, período no resto) | Baixo | 4 |
| **P3** | Queda 2022→2025: λ por ano e decomposição por classe | Expressão diferencial entre condições | Shift-share / Kitagawa | Local | Baixo | 5 |
| **P4** | Evento-estudo de aberturas e fechamentos de CNPJ no segmento de rua | Perturbação in situ (Perturb-map); o Δ previsto por λ é a "perturbação in silico" | Twinam 2017; Gruenewald et al. 2022 | Local (CNPJ com datas) | Médio–alto | 5 ou ED |
| **P5** | População presente: OD 2017 por hora → taxa por pessoa-hora | Normalização por tamanho de biblioteca | Hipp et al. 2018; Hanaoka 2018 | **Baixar** (pedir autorização) | Médio | 4 |
| P6 | Memória do lugar: dentro da classe, quanto o passado prevê; meia-vida do resíduo | Estado × tipo celular (com cautela) | Trajetórias de segmentos (Schnell et al. 2020) | Local | Baixo–médio | 5 |
| P7 | Curva de previsibilidade × escala de agregação | — | Song et al. 2010 | Local | Baixo | 6 |
| P8 | Registros de iniciativa policial como proxy de atenção policial (sensibilidade) | — | Viés de feedback | Local | Baixo | ED |
| P9 | SVG (nnSVG/SPARK-X) × Moran | Genes espacialmente variáveis | Moran | Local | Baixo | ED |

**Fora agora:** imagem como "histologia", transferência para outra cidade, OD/COMMOT, ablação do GNN.

### Gates de decisão (exploração, 77 distritos)

- **G1 (P1):** pelo menos 3 fenótipos com assinaturas distintas entre classes. O controle positivo deve se comportar como esperado (trânsito com máximo nas vias arteriais), e a validação pontual deve ser forte nos fenótipos bem geocodificados. **Se passar, "que crime" entra na tese.**
- **G2 (P2):** os perfis por período diferem entre classes além do nulo de permutação e se repetem entre 2024 e 2025. **Se passar, "quando" passa a ter duas escalas.**
- **G3 (P4):** sem pré-tendência e com efeito detectável. **Se passar, entra o ato C;** se não, o resultado vai para o ED como nulo informativo.
- **G4 (P3):** a queda se concentra nas taxas de classes específicas. **Se passar, entra a frase "o tecido é estável, as taxas se movem".**

### Cuidados técnicos

- A base de celular cobre quase todo FURTO/ROUBO-OUTROS com subtração de celular (99,7%). No P1, os BOs de celular saem dos fenótipos "outros" pela chave do BO.
- A supressão de coordenadas varia com o tipo de local (residências, estações). A atribuição usa contagens reconciliadas no setor; a validação pontual usa só os eventos geocodificados.
- No furto, a hora é imprecisa (a vítima percebe depois), então o relógio do tecido se apoia no roubo.
- Ficam fora: violência doméstica (D14); crimes de iniciativa policial (escopo); estupro (não sai em mapa). A lesão dolosa entra só fora de residências.
- Os registros do arquivo de 2026 fora do cofre (fatos de 2025 registrados em 2026) não são lidos no atlas (`guard.pre2026`). O efeito é subestimar levemente dezembro de 2025.

## 6. Pré-registro

- Os pilotos são exploratórios (D40) e usam os tipos já fixados, então não mudam os hashes do FREEZE-A.
- O que o autor escolher entra na A11 como candidato da família do atlas. Exemplos:
  - **A-R6:** o ranking das assinaturas se repete no cofre;
  - **A-R7:** o contraste de ritmos se repete no cofre.
- A confirmação roda no cofre antes do FREEZE-B.
- 2026 continua sendo teste de estabilidade.

## 7. Referências a verificar

Antes de usar, checar todas com `/ars-citation-check`. A afirmação "primeira aplicação do conjunto de ômica espacial a cidades" exige busca sistemática: a busca desta análise foi superficial.

- Weisburd, D. et al. (2024). Crime concentrations at micro places: a review of the evidence. *Aggression and Violent Behavior*.
- Andresen, M. A. et al. (2017). The trajectories of crime at places: understanding the patterns of disaggregated crime types. *J Quant Criminol*.
- Twinam, T. (2017). Danger zone: land use and the geography of neighborhood crime. *J Urban Econ*.
- Gruenewald, P. et al. (2022). Assessing the impacts of alcohol outlets on crime as a natural experiment. *Addiction*.
- (Autoria a confirmar) (2021). Unveiling the relationship between land use types and the temporal signals of crime: an empirical decomposition approach. *Environment and Planning B*.
- Hipp, J. R. et al. (2018). Using social media to measure temporal ambient population. *Justice Quarterly*.
- Hanaoka, K. (2018). New insights on relationships between street crimes and ambient population. *Environment and Planning B*.
- Schnell, C. et al. (2020). The influence of temporal specification on the identification of crime hot spots. *J Quant Criminol*.
- Delmelle, E. (2016). Mapping the DNA of urban neighborhoods. *Annals AAG* (precedente de metáfora biológica).
- Song, C., Qu, Z., Blumm, N. & Barabási, A.-L. (2010). Limits of predictability in human mobility. *Science*.
- Singhal, V. et al. (2024). BANKSY. *Nature Genetics*.
- Callaway, B. & Sant'Anna, P. (2021). Difference-in-differences with multiple time periods. *J Econometrics*.
- Kotliar, D. et al. (2019). cNMF. *eLife*.
- Newman, A. M. et al. (2019). CIBERSORTx. *Nature Biotechnology*.
- Dhainaut, M. et al. (2022). Perturb-map. *Cell*.
- Zhang, R. et al. (2014). A circadian gene expression atlas in mammals. *PNAS*.
- Brantingham, P. & Brantingham, P. (1995). Criminality of place: crime generators and crime attractors. *Eur J Crim Policy Res*.

## 8. Resultados dos pilotos

Rodada de 2026-10-19 nos 77 distritos de exploração (21.331 setores), 2022–2025, sem 2026 e sem o cofre. Código em `src/cityomics/atlas/fenotipo.py` e `perturbacao.py` (`cityomics atlas run fenotipo perturbacao`); saídas em `data/processed/atlas/fenotipo/` e `.../perturbacao/`. Os números são exploratórios (D40).

### Painel

- **15 fenótipos, 1,83 milhão de eventos em 2022–2025 (cidade inteira; as análises usam só a exploração).** Furto a pessoa (sem celular) 450 mil; furto de celular 404 mil; roubo de celular 310 mil; roubo a pessoa 170 mil; furto de veículo 162 mil; lesão dolosa fora de residência 85 mil; trânsito 55 mil; roubo de veículo 54 mil; comércio 35 mil; fios e cabos 31 mil; interior de veículo 30 mil; residência 22 mil; carga 10 mil; coletivo 6 mil; letal 5 mil.
- **Sobreposição com a base de celular:** 34–39% das linhas da base principal têm BO de celular (chave delegacia × ano × número). Essas linhas saíram dos fenótipos "outros".
- **Cobertura de coordenadas:** acima de 80% em 12 dos 15 fenótipos. As exceções:
  - residência: 26%, então a assinatura depende da reconciliação;
  - letal: 70%;
  - furto de celular: 78%.

### P1: cada classe de célula tem uma assinatura criminal → G1 **passa**

Classe mais enriquecida por fenótipo. Só entram classes com ≥ 2% do fenótipo e IC de bootstrap acima de zero. O valor é log2 do enriquecimento contra a média dos fenótipos, com a participação da classe entre parênteses:

| Fenótipo | Classes mais enriquecidas |
|---|---|
| Coletivo | Terminais +2,5 (6%); estações +2,3 (18%) |
| Furto de celular | Estações +1,6 (11%); vertical e misto +1,3 (18%); comércio médio +1,0 (20%) |
| Comércio | Comércio de rua médio +1,3 (24%); misto +0,9 (13%) |
| Roubo a pessoa | Comércio de rua popular +0,8 (19%) |
| Residência | Residencial horizontal médio +3,4 (31%) |
| Furto de veículo | Atacadista +2,2 (9%); residencial horizontal médio +1,7 (10%) |
| Letal | Residencial horizontal popular +1,5 (17%); terreno vago +1,5 (11%); favela +1,2 (7%) |
| Lesão dolosa | Residencial horizontal popular +1,4 (16%) |
| Roubo de veículo | Indústria +1,5 (10%); residencial popular +1,2 (14%) |
| Carga | Indústria +2,0 (13%); favela +1,9 (11%) |
| Trânsito (controle) | Indústria +0,8 (6%); vias arteriais +0,7 (7%) |
| Roubo de celular | Vertical e misto +0,4 (9%): o mais difuso |

- **11 classes distintas no topo.** A correlação entre os perfis de participação dos fenótipos tem mediana ρ = 0,58: há um esqueleto comum (comércio e ruas locais), com faces distintas.
- **Controle positivo.** O trânsito tem λ por km nas arteriais (1,50) maior que nas coletoras (0,69) e nas locais (0,62). O enriquecimento das arteriais é +0,70 (IC 0,44–0,90).
  - Ressalva: a classe mais enriquecida no trânsito é a indústria, cujos lotes têm frente para arteriais. O controle passa no critério definido, não como "a" classe do trânsito.
- **Validação pontual** (λ contra a taxa observada ligando cada ponto ao segmento e aos lotes lindeiros): mediana ρ = 0,85 entre tipos de lote em 12 fenótipos.
  - De 0,93 a 0,95: furto a pessoa, roubo de celular, furto de veículo.
  - De 0,62 a 0,74: carga, roubo de veículo, interior de veículo.
  - Ficaram fora (cobertura < 80%): residência, letal e furto de celular.
- **Programas (NMF, k = 4, estabilidade 0,96)**, cada um associado a uma composição:
  1. **Transporte:** coletivo + furto de celular → estações e terminais.
  2. **Centro denso:** furtos, comércio, roubo de celular → vertical e misto.
  3. **Logística periférica:** carga e veículos → terreno vago, residencial popular, indústria.
  4. **Residencial:** letal + residência → residencial horizontal.
  
  As associações são modestas (ρ 0,10–0,19).

**Leitura.** O tecido define *que* crime acontece, e não só quanto. Hubs de transporte "expressam" furto e coletivo. O centro denso expressa furto e comércio. O residencial médio expressa arrombamento. A periferia popular e informal expressa violência letal, lesão e roubo de veículo e de carga. Isso é a matriz-assinatura da ômica (classe × fenótipo), validada ponto a ponto.

### P2: o tecido tem relógio → G2 **passa para o furto; limítrofe para o roubo**

- **Teste:** contraste entre os perfis por período (madrugada, manhã, tarde, noite) das classes, contra 200 permutações dos períodos dentro do distrito. O nulo é conservador, porque preserva o ritmo de cada distrito.
- **Resultados por fenótipo:**

  | Fenótipo | p em 2024 | p em 2025 | Réplica 2024 × 2025 (r) |
  |---|---|---|---|
  | Furto de celular | 0,005 | 0,005 | 0,93 |
  | Roubo de celular | 0,005 | 0,07 | 0,90 |
  | Roubo a pessoa e trânsito | sem ritmo específico por classe | | |

  O trânsito sem ritmo próprio é coerente: o deslocamento é da cidade inteira.
- **Hora exata, roubo de celular** (75.508 eventos, 2024–2025):
  - **Residencial horizontal popular: 39% dos roubos entre 4h e 6h** (pico às 4h). Na favela o pico é às 5h e, no terreno vago, há outro pico às 4–5h;
  - comércio, verticais, serviços e ruas: pico entre 19h e 22h;
  - estações: pico às 18h.
- **Fim de semana × dia útil** (taxa por dia):
  - roubo de celular: misto residencial-comercial 1,6×, residencial popular 0,4×, arteriais 0,75×;
  - furto de celular: misto 1,75×; favela 2,1× e sem cadastro 2,5×.

**Leitura.** Na escala do dia, o "quando" é estruturado pelo tecido:
- a periferia é roubada na ida ao trabalho, de madrugada e em dia útil;
- o centro e o comércio, no fim da tarde;
- o misto, na noite de fim de semana.

É atividade rotineira com resolução de lote. Isso dá a tese das duas escalas: o dia é tecido e o mês é ruído.

### P3: o tecido é estável, as taxas se movem → G4 **passa**

- **Totais do celular:** caiu 20% de 2022 para 2025 nos setores de exploração (151,6 mil → 121,4 mil). A queda é do **roubo** (razão 0,60), não do furto (0,98).
- **Com a composição de 2025 fixa,** a queda não foi uniforme:
  - **caíram:** ruas locais (razão relativa 0,76; IC 0,65–0,87), residencial horizontal popular e de esquina (0,27–0,28), coletoras e comércio popular;
  - **ficaram estáveis em termos absolutos:** estações (86 → 87 por ano; razão relativa 1,27, IC 1,04–1,73), comércio de rua médio (70 → 71 por km) e misto (razão relativa 1,48, IC 1,09–2,30).
- **Concentração:** as três classes que mais contribuíram para a queda somam 21 pontos percentuais a mais do que sua participação em 2022.
- **Outros fenótipos:**
  - caíram: roubo de veículo (0,58), carga (0,56), interior de veículo (0,41), coletivo (0,44), comércio (0,48), residência (0,39);
  - subiram: furto a pessoa (1,36), lesão dolosa (1,50), trânsito (1,32).

**Leitura.** O recuo do roubo veio da malha difusa (ruas locais, residencial). Os polos (estações, comércio médio, misto) mantiveram a taxa. **O crime recuou para os seus nichos.** É expressão diferencial com o tecido fixo, e prepara 2026 (queda de 14% a 34% já declarada) como teste de estabilidade.

### P4: perturbação natural → G3 **não passa (nulo informativo)**

- **Desenho:** CNPJ do snapshot de 2025-12 (5,9 milhões de estabelecimentos, incluindo baixados), dos quais 3,07 milhões ligados a um lote pelo endereço. Ao todo, 158.663 segmentos de exploração e 1,04 milhão de eventos ligados.

| Tratamento | Segmentos tratados | Base (eventos/mês) | Pré-tendência (IC) | Efeito 0–11 meses (IC) | Efeito mínimo detectável |
|---|---|---|---|---|---|
| Abertura de bar/restaurante | 15.500 | 0,249 | −0,000 (−0,010; 0,006) | −0,005 (−0,019; 0,002) | 6% |
| Abertura de varejo | 26.732 | 0,206 | +0,001 (−0,004; 0,007) | +0,001 (−0,008; 0,006) | 4% |
| Fechamento de bar/restaurante | 18.459 | 0,244 | −0,001 (−0,012; 0,006) | −0,005 (−0,019; 0,003) | 6% |

**Leitura.**
- Sem pré-tendência, e o efeito de uma abertura ou fechamento isolado no crime do segmento em 12 meses é nulo: efeitos acima de 4–6% da base ficam excluídos.
- O contraste transversal (comércio com 70 roubos/km, residencial ≈ 0) reflete a composição acumulada do tecido, não a mudança marginal.
- **Ressalva forte:** o CNPJ inclui MEI e endereços de contador. Uma abertura no cadastro nem sempre é uma porta aberta na rua, e esse erro de medida atenua o efeito.
- Refinamento possível antes de concluir: só não-MEI e só lotes de uso comercial no IPTU.
- Por ora, o ato C fica fora. O nulo vai para o ED como "inércia do tecido", coerente com a persistência (a média histórica explica mais que o tecido).

### Decisão sugerida

| Gate | Resultado | Consequência |
|---|---|---|
| G1 (que crime) | Passa | Fig. 3 = matriz-assinatura + programas + validação por fenótipo |
| G2 (a que hora) | Passa (furto); limítrofe (roubo, com perfil horário nítido) | Fig. 4 = relógio do tecido; "quando" em duas escalas |
| G3 (perturbação) | Não passa (nulo com efeito mínimo detectável de 4–6%) | ED; ato C fora por ora |
| G4 (mudança) | Passa | Fig. 5 = estabilidade + "o crime recuou para os nichos" |

**A narrativa B se sustenta nos dados de exploração.** O que o autor decide:
1. **Adotar B** como tese (substituindo ou refinando D35).
2. **Candidatos à família do atlas na A11** (confirmação única no cofre):
   - **A-R6:** o ranking das participações por classe de cada fenótipo se repete no cofre (Spearman ≥ 0,7 na mediana dos fenótipos);
   - **A-R7:** o contraste de perfis por período do furto de celular é maior que o nulo de permutação no cofre;
   - **A-R8:** no cofre, a razão relativa 2022→2025 das estações e do comércio médio fica acima da das ruas locais.
3. **Refinar o P4** (não-MEI, uso comercial) ou encerrá-lo como nulo.
4. **Autorizar o download da OD 2017 (P5).** É a defesa mais pedida: estações e comércio médio precisam ser comparados por pessoa presente, e o relógio por pessoa-hora.

## 9. Resultados de P4 refinado, P5, P6 e P7

### P5: população presente (OD 2017, baixada com autorização do autor)

- **Construção:** presença e pessoas a pé na rua por setor × hora (`atlas/presenca.py`). Às 3 h, 12,2 milhões de pessoas presentes; na rua, 4,0 milhões de pessoas-hora por dia.
- **A ordem das classes sobrevive à multidão.** Spearman entre o ranking por km e o ranking por pessoa:

  | Exposição | Roubo de celular | Furto de celular |
  |---|---|---|
  | Pedestres | 0,75 | 0,86 |
  | Pessoas presentes | 0,84 | 0,90 |

  - O comércio médio continua no topo do furto também por pedestre.
  - Nas estações há 1,6× a densidade média de pedestres: parte do excesso, não todo.
- **O relógio não é o da multidão.**
  - A correlação mediana por classe entre o perfil horário do roubo e o dos pedestres é 0,03.
  - No residencial popular, 41% do roubo (dias úteis) cai entre 4 h e 6 h, contra 3% dos pedestres.
  - O risco por pedestre é 19× a média às 3 h e mínimo ao meio-dia.
  
  Leitura: é vigilância natural (guardianship), a vítima sozinha na rua escura, não volume de alvos.

### P6: memória do lugar

- **Variância entre setores do log da taxa:** 42% tecido, 48% memória estável além do tecido, 23% transitória.
- **Nos setores de muito crime,** a memória sobe para 58%.
- **Persistência do resíduo:** 0,70, 0,65 e 0,63 com 1, 2 e 3 anos de defasagem.
- **Leitura:** os lugares lembram. A média histórica explica mais que o tecido porque guarda essa memória, e o nulo do P4 mostra que ela não se move com mudanças marginais.

### P7: limite de previsibilidade (refina a tese)

- **"Onde e quando":** o ensemble alcança 87–99% do R² máximo sem modelo, em todas as escalas.
- **Dentro do setor:** o R² é 0,018, para um máximo sem modelo de 0,56. À primeira vista, há dinâmica mensal não capturada.
- **O teste de dispersão por setor explica:**
  - **96% dos setores** têm o mês a mês compatível com ruído de Poisson (índice de dispersão mediano 1,01 nos setores com ≥ 1 caso por mês);
  - o **1% de setores com mais crime** concentra 34% do crime e **88% do excesso de variância**.
- **Tese refinada:** o mês a mês é ruído em quase toda a cidade. A dinâmica mensal que existe mora nos polos (estações e centros comerciais), onde o ganho dos métodos emprestados aparece.

### P4 refinado

| Variante | Segmentos tratados | Efeito mínimo detectável |
|---|---|---|
| Não-MEI em lote comercial | 3,5–6,7 mil | 5–11% |

- Também nulo, sem pré-tendência. A ressalva do CNPJ como proxy de porta aberta fica menor, e o nulo vai para o ED9.

### Confirmação pré-especificada

- `atlas/confirmacao.py` implementa A-R1, A-R2, A-R5, A-R6, A-R7 e A-R8.
- A família de B é A-R1, A-R2, A-R6, A-R7 e A-R8.
- No ensaio em pseudo-cofre, todas as cinco são sustentadas com Holm; a A-R5 falha (ΔR² −0,018).
- A confirmação de verdade só roda com a A11 datada, uma vez.

## 10. Tese final e mapa das figuras

**Tese (D63):** o crime é um fenótipo do tecido urbano. A composição do lugar fixa onde, que crime e a que hora acontece. A história do lugar guarda uma memória que mudanças marginais não movem. O mês a mês é ruído de Poisson em quase toda a cidade, e a pouca dinâmica previsível mora nos polos.

| Figura | Ato | Afirmação central |
|---|---|---|
| 1 | Anatomia | São Paulo como tecido de 1,65 milhão de lotes |
| 2 | Tipos e arquitetura | 12 tipos estáveis (ARI 0,97), nichos e domínios |
| 3 | Fenótipo | Cada classe tem sua assinatura criminal; validação ρ 0,85 |
| 4 | Ritmo | O relógio do tecido é de vigilância, não de multidão |
| 5 | Estabilidade, memória e mudança | Tecido estável, lugares que lembram, taxas que se movem |
| 6 | Limites e confirmação | Mês a mês = Poisson fora dos polos; métodos no teto; quadro de confirmação |

**Extended Data:** benchmark, auditoria de equivalências, comunicação, multiverso, Knox/MISTy/Lee, co-ocorrência, teoria, fora da amostra, perturbação e painel.

**O que falta, e é do autor:**
1. Datar a A11 (`prereg/A11_DRAFT.md`, família de B) em `AMENDMENTS.md`.
2. Rodar `cityomics.atlas.confirmacao.confirmar()` uma vez.
3. FREEZE-A e FREEZE-B.
4. Busca bibliográfica sistemática antes de afirmar novidade.
5. Revisão do texto e das referências (`/ars-citation-check`).
