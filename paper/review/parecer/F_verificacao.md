# Agente F: verificação independente da versão revisada

**Objeto:** `paper/manuscript_src.md` (com legendas e Tabela 1), `paper/supplementary_src.md` e `paper/manuscript.md`, contra os JSON atuais de `data/processed/atlas/` e `prereg/selection_dev.json`. Este relatório só lê e confere: não editei o manuscrito nem o código. O único arquivo regenerado foi `paper/manuscript.md`, pelo `python paper/build.py` que a tarefa pedia.

**Contagem:**
- conferi cerca de 150 números do resumo, do texto, da Tabela 1, das legendas, dos Methods e do SI;
- 26 divergências ou imprecisões numéricas (seção a), nenhuma que inverta um achado;
- 11 problemas de coerência (seção b);
- 13 exageros ou omissões (seção d), dois de gravidade alta.

Os números que batem não estão listados. Na conferência eu também recalculei, a partir dos parquet atuais, três quantidades que não estão gravadas em JSON: a estatística da C5 (0,334), a auditoria de renda (36%, 3%, 26%, 7% e calibração em até 4,7%) e as capturas a 5% da área (53%, 52%, 52% e 65%). As três batem com o texto.

**Formato Nature Cities (`python paper/build.py`, saída 0):**

| Item | Valor | Limite |
|---|---|---|
| Título | 36 caracteres | 90 |
| Resumo | 149 palavras | 150 |
| Texto principal | 3.492 palavras | 3.500 |
| Methods | 2.997 palavras | 3.000 |
| Referências do texto principal | 49 (67 no total) | cerca de 50 |
| Legendas | 1.643 palavras | não verificado pelo build |

- Todas as chaves `{…}` resolvem: o build falharia se faltasse alguma, e não sobrou nenhuma chave em `manuscript.md`.
- Como a folga é de 1 palavra no resumo, 8 no texto e 3 nos Methods, toda correção abaixo precisa ser neutra em palavras ou compensada.
- A legenda mais longa é a do ED Fig. 10 (291 palavras). Vale conferir no guia da revista.
- No fonte, as legendas do ED Fig. 9 e do ED Fig. 10 não têm linha em branco entre elas (linhas 206–207) e saem como um parágrafo só.
- São 7 itens de exibição (6 figuras e a Tabela 1). Vale conferir o limite do tipo de artigo.

---

## (a) Divergências numéricas

Gravidade: **A**, muda a leitura de um resultado ou aparece no resumo; **M**, número errado ou atribuído à quantidade errada, sem mudar a conclusão; **B**, arredondamento, rótulo ou ambiguidade.

| # | Grav. | Frase (local) | Texto | Dado | Fonte (arquivo → chave) |
|---|---|---|---|---|---|
| 1 | M | "consistent with geocoded events at finer scale, also with disjoint halves of events (median Spearman ρ = 0.78)" (resumo) | 0,78 atribuído às metades | Metades disjuntas: mediana 0,76 entre tipos de lote. O 0,78 é a checagem com todos os eventos | `fenotipo/identificacao.json` → `metades.mediana_painel_A_para_B_lotes` = 0,764; `assinaturas.json` → `gate_G1.validacao_mediana_lotes` = 0,784 |
| 2 | M | "For 15,708 exploration tracts with at least one expected event per year" (Methods, Persistent effect) | 15.708 | 15.929 | `fenotipo/memoria.json` → `setores`; `robustez.json` → `persistencia.n_total.setores` |
| 3 | M | "a cross-term (−13%) absorbs the covariance" (Methods) | −13% (Results diz −11%) | −11,5% | `memoria.json` → `partes.covariancia` = −0,1147 |
| 4 | M | "it gave 18 clusters; three with less than 0.3% of parcels were merged" (Methods, Parcel types) | 18 e 3 | 17 clusters e 2 fundidos (17 − 2 + vertical = 16) | `identificacao.json` → `tipos.reproducao_final.clusters_leiden` = 17, `.fundidos` = 2 |
| 5 | M | "e, Tissue domains (… k-means, k = 8)" (legenda da Fig. 2); "k-means (k = 8, chosen by silhouette)" (SI) | k = 8 | k = 7 (a silhueta máxima é em 7) | `dominios_2025.json` → `k` = 7, `silhueta` |
| 6 | M | "rail stations (0.92, 0.71–1.23) … kept pace with the city" (Rates move) | estações de trilho | 0,92 é o grupo estações + terminais. Só trilho dá 0,84 (0,62–1,15) | `robustez.json` → `queda_por_desfecho.celular_roubo.grupos.estacoes` e `.classes.n_trilho` |
| 7 | M | "fell faster … on residential classes taken together (0.40, 0.22–0.73) … and [slower] in favelas (1.23)" | as favelas aparecem como coisa separada | O grupo "residencial" inclui as favelas (`grupos.py`: res_horizontal + res_vertical_alto + FAVELA) | `robustez.json` → `queda_por_desfecho.celular_roubo.grupos.residencial`; `src/cityomics/atlas/grupos.py` |
| 8 | M | "With composition fixed at 2025 (Fig. 5e), … Phone robbery fell faster …" | razões do roubo citadas junto da Fig. 5e | A Fig. 5e plota o crime de celular total (`queda_celular.parquet`): por exemplo, estações de trilho 1,27 na figura contra 0,92 no texto | `fenotipo/queda_celular.parquet` → `razao_rel`; `figures/fig5.py` l. 111 |
| 9 | M | "Simulations with known rates recovered the order of classes (median ρ = 0.95) but, under district-level risk, not their absolute rates (median error 33%)" | 0,95 lido como valendo também com risco de distrito | Com risco de distrito, ρ = 0,84 e a cobertura dos IC de 95% é de 4%. No cenário coerente, a classe do topo nunca é recuperada | `identificacao.json` → `simulacao.celular_2025.cenarios.b_risco_distrito…spearman_taxas_todas` (mediana 0,838); `simulacao.celular_2025.cobertura.b_risco_distrito.taxas_mediana` = 0,04; `b2_risco_distrito_coerente.topo_taxa_km_recuperado` = 0 |
| 10 | M | "95% intervals within −7% to +8% of the baseline rate in all six variants" (Rates move); "changes of 5–9% cannot be excluded" (Discussion) | −7% a +8% | Bate com `perturbacao/evento_estudo.json` (−6,7% a +8,4%). O recálculo atual, com bootstrap da razão, dá −5,1% a +10,4% (abre bar, estrito: −3,5% a +10,4%). A Discussão mistura o MDE (5–9%) com o que o IC não exclui | `perturbacao/evento_estudo.json` → `*.ic_efeito / base`; `ritmo_queda.json` → `evento_estudo.*.ic_efeito_rel`; `*.mde_relativo` |
| 11 | M | "removed 13% of within-tract variance, so ceilings and rejection rates … are conservative" | 13% | 13% só vale com ausência ao acaso. Com ausência crescente com o crime do setor, sai 35% | `reconciliacao.json` → `ocultacao.mar.razao_var_dentro_agregada` = 0,873; `ocultacao.mnar_crime.razao_var_dentro_agregada` = 0,648 |
| 12 | M | "Types were stable across subsamples (ARI ≥ 0.95)" (Results); "ARI = 0.96 … for the final types" (Methods, legenda da Fig. 2f); SI: "the 16 final types with ARI = 0.96 (minimum 0.91), and each subsample agreed with the final typing with ARI = 0.91–0.98" | ≥ 0,95; 0,96 (mín. 0,91); 0,91–0,98 | Clusters brutos: média 0,950 e mínimo 0,907 (não é "≥"). Tipos finais: pares 0,976 (mín. 0,964); contra a tipagem final, 0,967–0,990 | `tipagem_2025.json` → `estabilidade."0.02"`; `identificacao.json` → `tipos.ari_pares_tipos_finais`, `tipos.ari_contra_final` |
| 13 | M | Tabela de Jaccard por tipo (SI) | ex.: "middle standard, with a service business 1.00 / 0.40"; "high standard 0.94 / 0.60"; "Mixed res. and commercial 0.99 / 0.52"; "with manufacturing 0.57 / 0.41"; "wholesale 0.40 / 0.29"; "middle std., home business 1.00 / 0.90" | 0,996 / 0,883; 0,949 / 0,926; 0,992 / 0,961; 0,684 / 0,553; 0,471 / 0,310; 0,998 / 0,969. A tabela parece de outra rodada | `identificacao.json` → `tipos.jaccard_por_tipo.*` |
| 14 | B | "ARI = 0.99" para a reprodução da tipagem (SI) | 0,99 | 0,9999 | `identificacao.json` → `tipos.reproducao_final.ari_vs_final_registrado` |
| 15 | B | "raw clusters agreed with ARI = 0.95 (minimum 0.90)" (SI) | mín. 0,90 | 0,907 | `tipagem_2025.json` → `estabilidade."0.02".ari_min` |
| 16 | B | "the rarer commercial and service types were the least stable" (Results) | comércio e serviços | O menos estável é o terreno vago de esquina (Jaccard 0,06) | `identificacao.json` → `tipos.jaccard_por_tipo."Terreno vago de esquina"` |
| 17 | B | "rising to 82% on the rail network" (Introdução) | 82% | 81% em 2022–2025 (não há valor de 2025 gravado) | `reconciliacao.json` → `recorte.fracao_sem_coordenada_por_estrato_2022_2025.trilhos` = 0,812 |
| 18 | B | "held when one half … was used for fitting and the other for checking (ρ = 0.83; Extended Data Fig. 10b)" | 0,83 citado junto do ED 10b | 0,83 é entre todas as classes, mas o ED 10b mostra tipos de lote (0,77) | `identificacao.json` → `metades.celular_2025.A_para_B_todas_media` = 0,827 e `A_para_B_lotes_media` = 0,771 |
| 19 | B | "88% expected, 86% observed" (Month-to-month) | 86% observado | A Fig. 6c usa o excesso truncado em zero, e nela o observado no 1% do topo é 88%; o texto usa a versão sem truncar | `robustez.json` → `escala_do_excesso.parte_excesso_top1_observada` = 0,859; `previsibilidade.json` → `dispersao_setor_mes.parte_do_excesso_no_top1pct` = 0,881 (`figures/fig6.py`, `panel_concentracao`) |
| 20 | B | "where it reaches 0.78 and the ensemble explains 0.03; in the other 99% … 0.08–0.19" | 0,78; 0,03; 0,08–0,19 | Não está em nenhum JSON atual; só no relatório A, §6. Não depende das duas correções, mas não é reproduzível a partir das saídas | `review/parecer/A_reconciliacao.md` §6 |
| 21 | B | "and the best single model, gradient boosting on core covariates, by 5%" (benchmark) | lido como "o ensemble supera o melhor modelo único em 5%" | O ensemble supera o LightGBM núcleo em 1,6% (0,2372 contra 0,2411); o LightGBM núcleo supera o GLM em 4,9% | `prereg/selection_dev.json` → `crps_medio` |
| 22 | B | "Best single model under the registered CRPS formula; third under the corrected CRPS" (SI Tabela 1, GNN) | terceiro | É segundo entre os modelos únicos (terceiro só contando o ensemble) | `selection_dev.json` → `crps_medio`: lgbm_nucleo 0,2411; gnn 0,2420; lgbm_completo 0,2422 |
| 23 | B | "For lethal violence at district scale, no model improved on the negative binomial baseline" × legenda do ED 5g: "Skill against the historical mean" | GLM no texto, média histórica na legenda | Contra o GLM, nenhum melhora (Holm). Contra a média histórica, todos melhoram | `data/processed/modelo/resultados_distrito_trimestre_2025.json` → `letal.contra_glm` |
| 24 | B | "Openings and closures of bars, restaurants and shops" | fechamentos de lojas | Fechamentos só de bares e restaurantes; de varejo, só aberturas | `perturbacao/evento_estudo.json` (variantes `abre_varejo`, `fecha_bar`; não há `fecha_varejo`) |
| 25 | B | "the Brier score of a count of at least 0.5" (Methods) × "Brier score of at least one event" (legenda do ED 4) | duas definições | P(Y ≥ 1) contra 1{y ≥ 0,5} (o SI está certo) | `supplementary_src.md`, "Scores, as implemented" |
| 26 | B | "class rates (median imputation interval 4% of the district-bootstrap interval)" | 4% | 4,5% | `reconciliacao.json` → `atribuicao_2025.largura_imputacao_sobre_bootstrap_mediana` = 0,0449 |

Nota ao item 10: os dois JSON são posteriores à correção das ruas. `ritmo_queda.json` foi gravado às 02:08 de 21/10 e lê o `evento_estudo.json` das 00:59 como "publicado". Os dois diferem no bootstrap (razão por réplica contra IC do efeito ÷ base pontual) e um pouco nos controles (119.359 contra 119.372). O autor precisa escolher uma versão e usá-la no texto, no ED Fig. 3 e no SI.

---

## (b) Problemas de coerência

1. **Fig. 5e contra o texto** (item a8). O texto discute o roubo de celular, mas a figura mostra o crime de celular total. Ou a figura passa a mostrar o roubo (`robustez.json → queda_por_desfecho.celular_roubo`), ou o texto cita a Fig. 5e só para o total e remete o roubo a outro painel.
2. **"Low-standard houses".** O glossário define *low-standard housing* com ou sem negócio registrado, mas o texto usa "low-standard houses" para o tipo *sem* negócio (roubo de veículo, +2,2) e "low-standard houses with a registered business" para o outro. Quem lê o glossário entende o grupo inteiro. Ver d1: a solução coerente é relatar os dois tipos juntos.
3. **"Residential classes"** inclui as favelas no código, mas o texto as trata como grupo à parte (item a7). Também não há definição de "residential classes" no glossário.
4. **Fig. 4c não é citada** no texto. A frase "The rhythm does not follow the crowd. Across classes, the median correlation…" deveria remeter a ela. As outras remissões das Figs. 4 e 6 conferem com as legendas: 4a (teste do furto), 4b, 4d, 4e e 4f; 6a, 6b, 6c (com o ED 10d), 6d e 6e.
5. **Definição órfã nos Methods.** "'Fitted jointly' means …" (Composition-aware attribution) define um termo que os Results não usam mais (R9). Cortar a frase libera cerca de 25 palavras nos Methods, a seção com menos folga.
6. **Fig. 6e.** O plano (R16) mandava levar a auditoria de renda ao Extended Data, mas ela continua como Fig. 6e. Não é erro; só precisa constar no registro como decisão.
7. **Checagem sem modelo.** "19% of weekday robberies with an exact hour" se refere a roubos de celular (53.912 eventos = `presenca_2023.json → eventos.roubo_hora_exata`). O texto deveria dizer "phone robberies".
8. **Estabilidade da tipagem com três medidas diferentes.** "ARI ≥ 0.95" nos Results, "0.95/0.96" nos Methods e na Fig. 2f, "0.95 (min 0.90)" e "0.96 (min 0.91)" no SI. Uma só fonte (`identificacao.json → tipos`) e um só par de números, com a medida nomeada (entre subamostras ou contra a tipagem final).
9. **Rascunho da A11 desatualizado.** `prereg/A11_DRAFT.md` ainda traz "12 types", "OD 2017" e os valores antigos do ensaio (0,92; 0,63; 0,85; 0,19; 0,82). O `confirmacao_ensaio.json` atual dá 0,906; 0,456; 0,854; 0,209; 0,729. Isso precisa ser corrigido antes de datar a A11.
10. **Nomes internos no SI.** A Tabela 1 do SI ainda diz "Laya-FT, Laya-ZS".
11. **Frases da versão antiga:** nenhuma sobreviveu no manuscrito nem no SI. Procurei "middle-standard retail", "19 times", "03:00", "only 4%", "too sparse", "−14% to +5%", "spread across the residential", "12 parcel types", "19 cell classes", "ARI = 0.973", "0.93", "Seattle/Boston" e "not a lever". O único "12 types" está no SI e descreve, com razão, a tipagem anterior.

---

## (c) Cobertura do parecer

| Item | Situação | Justificativa |
|---|---|---|
| R1 | atende | Resumo, Results e Discussão falam em variação que excede o ruído no topo e em modelos que capturam pouco. O teto é definido como limite, não como meta. |
| R2 | atende em parte | Imputações, ocultação de coordenadas, nulo pela reconciliação, escores fracionários e versões só geocodificadas estão feitos. O texto relata só a ocultação ao acaso (13%) e omite os 35% com ausência dependente do crime (a11). |
| R3 | atende em parte | Simulação, número de condição, exposições alternativas e efeito de distrito estão feitos. O texto omite o colapso da cobertura dos IC sob risco de distrito e a colinearidade dos dois tipos populares, que sustenta achados de destaque (d1, d3). |
| R4 | atende em parte | O resumo diz "consistent with" e as metades e a ocultação foram feitas. Falta corrigir o número do resumo (a1). O controle positivo residencial (19% geocodificado) e a taxa das estações dependem da alocação, sem ressalva (d5). |
| R5 | atende em parte | OD 2023, bootstrap por domicílio, separação entre a pé e bicicleta e OD 2017 como sensibilidade estão feitos, e os mecanismos aparecem como alternativas. A sensibilidade a σ não é relatada, e o ρ varia de 0,49 a 0,81 com σ de 150 a 600 m (`ritmo_queda.json → pedestres.pontos`, OD 2017) (d10). |
| R6 | atende | Diz "no detectable change", nomeia o estimador, dá o MDE e passa o tema ao ED e ao SI. Resta escolher uma versão dos IC (a10). |
| R7 | atende em parte (autor) | A cronologia está documentada (SI, Tabela 2), e a relação entre o hold-out e a janela prospectiva está clara. A confirmação está pendente por protocolo e o rascunho da A11 está desatualizado (b9). |
| R8 | atende | Há nulo simulado pela reconciliação (1,7% e 2,2%), poder e sobredispersão comum. |
| R9 | atende | Os Results dizem "fitted each with the same exposures". Sobra a definição órfã nos Methods (b5). |
| R10 | atende em parte | A estabilidade dos tipos finais é relatada, mas os números não batem com `identificacao.json` (a4, a12, a13). |
| R11 | atende | A concentração da queda foi medida (29% contra 22% sob queda proporcional) e saíram "spread across" e a comparação com Seattle e Boston. |
| R12 | atende | Há alternativas de exposição que mudam a distribuição espacial (área, perímetro, domicílios), com ρ ≥ 0,996. |
| R13 | atende | Tabela 1 do SI completa. |
| R14 | atende | A disponibilidade temporal está documentada, com a ressalva "retrospective rather than strictly real-time". |
| R15 | atende | O estado é definido primeiro em termos estatísticos ("persistent heterogeneity … a label for what typing misses"). |
| R16 | atende em parte | A Fig. 4 abre pelo teste do furto e a violência letal foi para o ED 5g. A auditoria de renda continua na Fig. 6 (b6), a Fig. 4c não é citada (b4) e a Fig. 5e não bate com o texto (b1). |
| R17 | não atende (autor) | Autores, ética, financiamento, CRediT, uso de IA, DOIs e repositório continuam como marcadores. |
| R18 | atende | Gorr & Lee, Quick et al., Albors Zumel et al., De Nadai et al., Wu et al. e Bernasco & Steenbeek estão citados, além de Quick 2018 e Andresen 2007 nos Methods. Ficaram 49 referências no texto principal. |
| §4.2 | atende | O atlas é o eixo, e a previsão aparece como alcance e limite na última seção dos Results e num parágrafo da Discussão. |
| §4.3 | atende | O furto vem primeiro e é o teste pré-especificado. O roubo tem os nulos em blocos, e o pré-amanhecer está marcado como exploratório. |
| §4.4 | atende | — |
| §4.5 | atende | Negócios ficaram com uma frase no texto e o ED 3; a camada de linguagem, com uma frase nos Methods; a comunicação L–R, no ED. |
| §4.6 | atende | A defesa da analogia está concentrada num parágrafo da Discussão. |
| §4.7 | atende | A mensagem central foi adotada no resumo e no primeiro parágrafo da Discussão, com redação ajustada. |
| §8 | não implementado (autor) | Decisão registrada no plano. |

---

## (d) Exageros e omissões, com a correção proposta

**d1 (alta). "Low-standard houses with a registered business" na violência letal e na carga.** A separação entre os dois tipos populares não é identificada:
- as exposições dos dois tipos têm r = 0,85 (`identificacao.json → condicionamento.correlacao_exposicoes_pearson_extremos`), e as estimativas, r = −0,73 (`condicionamento.fisher.pares_correlacao_estimativas`);
- na violência letal, o IC do tipo "com negócio" começa em +0,0006, quase em zero. O tipo irmão tem +1,58, com IC de −2,83 a +2,71 (`assinaturas.parquet`);
- nas simulações com taxas conhecidas, a classe mais enriquecida da violência letal é recuperada em só 25% das réplicas, mesmo no Poisson puro, e em 30% com risco de distrito. A da carga, em 33% com risco de distrito (`simulacao.painel.cenarios.*.resumo.{letal,carga}.topo_enriquecido_recuperado`);
- a carga tem a pior checagem fina (ρ = 0,44), e a violência letal não pode ser checada (66% geocodificada);
- a massa troca de rótulo entre os dois tipos conforme o crime: o roubo de veículo vai para o tipo "sem negócio" e a carga e a violência letal, para o tipo "com negócio";
- juntando os três tipos populares, o enriquecimento é +1,8 na violência letal, +1,7 na carga e +1,6 no roubo de veículo (recalculado de `assinaturas.parquet`).

Correção (Results; quase neutra em palavras):
> "Lethal violence, 66% geocoded, is enriched on low-standard houses, vacant land and favelas (log₂ enrichment +1.8, +1.9 and +1.4), cargo theft and robbery on the same houses and favelas (+1.7 and +2.0), vehicle theft on houses with wholesale businesses (+2.1), vehicle robbery on low-standard houses (+1.6) …"

Correção (Limitations, no lugar de "and classes with little crime have rates and hourly profiles that the data barely identify"):
> "and classes with little crime or correlated exposures, such as low-standard houses with and without a registered business, are barely identified."

A legenda da Fig. 3 e a Fig. 3b devem seguir o mesmo agrupamento, ou dizer que a separação entre os dois tipos não é identificada.

**d2 (alta). Efeito de distrito.** A frase "A multiplicative risk level per district preserved the order of classes (ρ = 0.96)" esconde que:
- a classe do topo muda: com efeito de distrito, o misto com indústria tem 20,4/km e o vertical, 15,0;
- a taxa da indústria se multiplica por 12 (de 0,69 para 8,1) e a das ruas locais dobra (`robustez.json → efeito_distrito.celular_2025.taxas_com`);
- 4 dos 15 crimes trocam de classe no topo;
- sob risco de distrito, os IC por bootstrap cobrem a taxa verdadeira em cerca de 4% das réplicas, o que tira o sentido de intervalos como "19–56" (a9).

Correção (neutra em palavras):
> "A multiplicative risk level per district preserved the broad order of classes (Spearman ρ = 0.96) but changed the top class, lowering central rates to 15 per km on high-rise buildings and 36 per station. Simulations with known rates recovered the order of classes (median ρ = 0.95; 0.84 under district-level risk) but, under district-level risk, neither absolute rates (median error 33%) nor interval coverage, so we interpret orders and shares."

No resumo, "that survives district-level risk" pode ficar, porque se refere à ordem.

**d3 (média). Pré-amanhecer.**
- No modelo, 41% (30–60%) do roubo do tipo popular cai entre 04h e 06h. Na checagem sem modelo, 19% (16–22%). O texto diz que a checagem "supports the direction", mas a magnitude é metade (`ritmo_queda.json → relogio_ic.pre_amanhecer`).
- Os tipos populares têm taxa de roubo de celular quase nula: 1,5 × 10⁻⁵/km para o tipo com negócio e 0,017/km para o sem negócio. É exatamente o caso que a própria Limitation diz ser mal identificado.
- A janela de 04h a 06h coincide com a saída para o trabalho na periferia.
- A Discussão tira dali uma sugestão de política, a iluminação.

Correção (Results):
> "… whereas the model, for classes with little phone crime, places the peak on low-standard houses and favelas before dawn (Fig. 4b). A model-free check supports the direction, at half the magnitude: … 19% of weekday phone robberies …"

Correção (Discussion):
> "If confirmed, the second would call for testing measures that raise guardianship at those hours, when early commuters leave home, such as street lighting{chalfin2022}."

**d4 (média). Valor da previsão.** "So most of the operational value of predictive policing at the scale of tract-months lies in the map of past crime" afirma mais do que o estudo mede:
- não se mediu valor operacional, só a captura;
- os números são de desenvolvimento, em 2025, com os 96 distritos;
- o ensemble já usa o histórico.

Correção (neutra em palavras):
> "Monthly forecasts improved probabilistic scores by about 6% but added about one percentage point to the share of crime captured in development, so at the scale of tract-months most of what they offer for flagging places is already in the map of past crime, a comparison that early-warning systems for temporary hot spots have faced before{gorr2015}."

**d5 (média). Estações e controles positivos dependem da reconciliação.**
- A taxa das estações de trilho cai de 73 para 36 por estação só com eventos geocodificados (`reconciliacao.json → atribuicao_2025.classes.n_trilho.geocodificado` = 35,6). Isso acontece porque 81% do estrato de trilho não tem coordenada e é alocado só a setores a até 250 m de uma estação.
- O controle positivo residencial (19% geocodificado) também é em boa parte construído pela alocação por estrato (R4).

Correção:
> "… and rail stations 73 per station (39–109; 36 with geocoded events only)."
> "Crime types defined by place behave as positive controls, the residential one resting mostly on reconciled events: …"

**d6 (média). "Each class of cell a distinct crime profile" (resumo).** Várias classes têm taxas quase nulas e não identificadas.

Correção (−2 palavras):
> "A composition-aware model gives classes of cell distinct crime profiles that survive district-level risk …"

**d7 (média). Suavização pela reconciliação** (a11).

Correção:
> "… recovered tract-month counts (r = 0.99) but removed 13% of within-tract variance (35% when missingness rose with tract crime), so ceilings and rejection rates of reconciled counts are conservative."

**d8 (média). Evento-estudo** (a10 e a24).

Correção (Results):
> "Openings and closures of bars and restaurants and openings of shops on street segments were followed by no detectable change …"

Correção (Discussion):
> "… although changes of up to about 8% (10% in the strictest variants) cannot be excluded."

Ajustar os números à versão escolhida.

**d9 (baixa). Persistência "accounts for more" (resumo, introdução, Discussão).**
- A margem é pequena em todos os setores: 46% contra 42%, 44% contra 40% só geocodificado e 45% contra 41% com imputações, com um termo cruzado de −11%. Não há IC para a partição.
- A afirmação é sólida nos setores de contagem alta (60% contra 23%).
- Sugestão: dar o IC da partição por bootstrap de distritos.

Correção (resumo, neutra):
> "Persistent differences between places that composition does not explain account for as much of how much crime a tract records, and more where crime concentrates."

Atenção: essa versão tem mais palavras; compensar no resumo ou manter o original se o IC sustentar "more".

**d10 (baixa). Denominador de pedestres.** A Spearman de 0,64 é para σ = 300 m. Com a OD 2017, ela vai de 0,49 (σ = 150 m) a 0,81 (σ = 600 m). A ordem relativa por pedestre é sensível à suavização.

Correção (SI ou Methods, se houver espaço):
> "ρ ranged from 0.49 to 0.81 for σ between 150 and 600 m (2017 survey)."

Vale rodar o mesmo com a OD 2023.

**d11 (baixa). "Typing describes what a place is" e "Parcel types were fixed without crime data" (Introdução).**
- A segunda é verdadeira quanto ao procedimento, mas a tipagem foi refeita depois de os resultados de crime da anterior serem conhecidos. Isso está nos Methods e no SI, não na Introdução.
- Os 8 de folga podem pagar a correção:
> "Parcel types were defined without crime data (Methods) …"

**d12 (baixa). Favelas.** "Although they do not depend on how it is constructed" generaliza a partir de cinco construções.

Correção:
> "… although they did not change under five alternative constructions."

**d13 (baixa). Omissão nas Limitations.** A cobertura nominal dos intervalos não vale sob heterogeneidade de distrito (d2), e o texto não diz isso em lugar nenhum. Se d2 for aceita no Results, basta.
