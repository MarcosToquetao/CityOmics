# Agente D: literatura e posicionamento (R18)

**Data:** 2026-10-20. **Escopo:** item R18 e seção 9 do parecer (S16–S21), mais uma busca curta por antecedentes próximos. Nenhum arquivo do projeto foi editado além deste relatório.

**Método.** Os metadados vêm da Crossref (`api.crossref.org/works/<DOI>`) e do OpenAlex (`api.openalex.org/works/doi:<DOI>`), com o resumo reconstruído do `abstract_inverted_index`. Quando os dois não traziam o resumo, usei a Europe PMC (Rotaru et al.), a Semantic Scholar (Quick, Li & Brunton-Smith; Hipp & Kim, só a primeira frase), uma versão do OpenAlex depositada no eScholarship (Hipp & Kim, resumo completo) e o registro do Figshare da CMU (Gorr & Lee, versão de working paper). Nenhum PDF foi baixado. Os resumos abaixo são paráfrases minhas. A seção 5 lista o que não consegui verificar.

**Estado atual.** O texto principal tem 50 referências e 3.290 palavras (limite de 3.500). Outras 9 referências aparecem só em Methods.

---

## 0. Recomendações em uma tabela

| # | Obra | Decisão | Onde | Efeito na contagem |
|---|---|---|---|---|
| 1 | Gorr & Lee 2015 (busca) | **citar** | Discussão, previsão | +1 |
| 2 | Quick, Law & Li 2019 (S16) | **citar** | Introdução, frase do "mixed" | +1 |
| 3 | Albors Zumel et al. 2026 (S18) | **citar** | Resultados, benchmark | +1 |
| 4 | De Nadai et al. 2020 (S21) | **citar** | Discussão, transferência | +1 |
| 5 | Wu et al. 2022 (S17) | **citar** (é a primeira a cortar se faltar espaço) | Resultados, benchmark, na mesma frase de S18 | +1 |
| 6 | Bernasco & Steenbeek 2017 (busca) | **citar** | Resultados, mês a mês | +1 |
| 7 | Stucky & Ottensmann 2009 (busca) | **trocar por andresen2017** | Introdução, frase "Facility and land-use studies…" | 0 |
| 8 | Quick, Li & Brunton-Smith 2018 (busca) | citar **só em Methods** | Methods, NMF | 0 (Methods) |
| 9 | Andresen 2007 (busca) | citar **só em Methods** | Methods, enriquecimento | 0 (Methods) |
| — | Rotaru et al. 2022 (S19) | **não citar** | guardar para a resposta aos revisores | — |
| — | Varese & Zeng 2024 (S20) | **não citar** | — | — |
| opc. | Ceccato & Moreira 2021; Hipp & Kim 2019 | opcionais | Resultados (estações; relógio do roubo) | +1 cada, com corte extra |

**Para manter 50 no texto principal:** seis referências puramente técnicas, que já estão (ou podem entrar) em Methods, saem do texto principal. São elas: `traag2019`, `gneiting2007`, `cochran1954`, `callaway2021`, `gale2016` e `metro2017` (seção 3). A conta fica em 50 − 6 − 1 (andresen2017) + 1 (stucky2009) + 6 = **50**. As frases novas somam cerca de 70 palavras (texto principal passaria de 3.290 para cerca de 3.360).

---

## 1. Antecedentes listados no parecer (S16–S21)

### S16. Quick, Law & Li (2019) — **citar**

**Ficha (Crossref e OpenAlex conferem):** Quick, M., Law, J. & Li, G. Time-varying relationships between land use and crime: a spatio-temporal analysis of small-area seasonal property crime trends. *Environ. Plan. B Urban Anal. City Sci.* **46**(6), 1018–1035 (2019). Online em 4 dez. 2017. https://doi.org/10.1177/2399808317744779. A ficha do parecer está correta.

**O que estudou e achou.** Ajustaram um modelo bayesiano espaço-temporal a 12 estações do ano de crimes contra o patrimônio em pequenas áreas, com coeficientes de uso do solo que variam por estação. Parques têm associação mais forte na primavera e no verão, e bares e restaurantes no outono e no inverno. O uso do solo pesa muito mais no padrão espacial do que no espaço-temporal. O resumo não nomeia a cidade, e eu não a verifiquei.

**Com que o manuscrito conversa.**
- Introdução: "evidence on whether the effect of a place changes with the hour is mixed{haberman2015,bernasco2017,vansleeuwen2021}".
- Num segundo plano, a divisão entre o *onde* (composição e histórico) e o mês a mês.

**Ameaça à originalidade?** Não ameaça "Few studies read the full composition of a city, all its crime types and the hour together": Quick et al. usam um único grupo de crime, poucos usos do solo como covariáveis e a estação do ano, não a hora. O estudo mostra, porém, que a combinação "uso do solo × tempo" já foi modelada. O texto não deve apresentar essa combinação como nova, e hoje não apresenta.

**Frase proposta (introdução):**
> …and evidence on whether the effect of a place changes with the hour or season is mixed{haberman2015,bernasco2017,vansleeuwen2021,quick2019}.

**Reuso opcional (não muda a contagem),** no fim do parágrafo do mês a mês: "…as land use shaped where property crime occurred more than when{quick2019}."

### S17. Wu et al. (2022) — **citar** (prioridade abaixo de S18)

**Ficha:** Wu, J., Abrar, S. M., Awasthi, N., Frías-Martínez, E. & Frías-Martínez, V. Enhancing short-term crime prediction with human mobility flows and deep learning architectures. *EPJ Data Sci.* **11**, 53 (2022). https://doi.org/10.1140/epjds/s13688-022-00366-2.
- O parecer omitia autores, volume e número do artigo.
- A Crossref grafa "Frias-Martinez" sem acentos. O OpenAlex traz "Frías-Martínez".

**O que estudou e achou.** Testaram fluxos finos de mobilidade de uma empresa de inteligência de localização como preditores de curto prazo, em várias cidades, tipos de crime e arquiteturas neurais. A mobilidade elevou o F1 de 2% a 7%. As arquiteturas neurais superaram a regressão não neural em no máximo 2%.

**Com que conversa.** Com "Forecasting methods from seismology, epidemiology, ecology, econometrics and machine learning did little better than simple baselines" e "the best model improved the continuous ranked probability score … by 4%".

**Ameaça à originalidade?** Sim, para a mensagem "modelos complexos melhoram pouco", que já está documentada. O que o manuscrito acrescenta é outra coisa: o teto de ruído e a separação entre variação entre setores e dentro do setor. É o que o parecer pede no item 9.2.

**Frase proposta:** ver S18. As duas entram numa única frase.

### S18. Albors Zumel, Tizzoni & Campedelli (2026) — **citar**

**Ficha:** Albors Zumel, A., Tizzoni, M. & Campedelli, G. M. Deep learning for crime forecasting: the role of mobility at fine-grained spatiotemporal scales. *J. Quant. Criminol.* **42**(3), 511–568 (2026). Online em 22 set. 2025. https://doi.org/10.1007/s10940-025-09629-3. A ficha do parecer está correta; faltava só o número 3.

**O que estudou e achou.**
- Dados: Baltimore, Chicago, Los Angeles e Filadélfia, 2019–2023, numa grade de 0,2 km².
- Modelo: uma ConvLSTM prevê ocorrências 12 horas à frente, a partir de sequências de 14 e de 2 dias.
- Baselines: regressão logística, floresta aleatória e LSTM.
- Achados: a mobilidade melhora a previsão, sobretudo com sequências curtas. O melhor resultado combina mobilidade com dados sociodemográficos.

**Com que conversa.** Com a conclusão de que o mês a mês é "too sparse to detect or forecast" e com a delimitação que R1 vai impor: crime de celular, setor × mês.

**Ameaça à originalidade?** Não. Ela delimita o alcance: em escalas finas e horizontes curtos há ganhos relatados. Isso não deve ser comparado diretamente com o CRPS por setor-mês (métricas e escalas diferentes, como lembra o parecer).

**Frase proposta (Resultados, logo após "did little better than simple baselines"):**
> Elsewhere, neural architectures improved on regression by at most 2%{wu2022}, and mobility data improved 12-hour forecasts on 0.2-km² grids{alborszumel2026}; neither scale nor metric matches ours.

Se houver vaga para uma só, fica S18 e a frase termina em "…on 0.2-km² grids{alborszumel2026}, a scale our tract-month benchmark does not test."

### S19. Rotaru et al. (2022) — **não citar**

**Ficha:** Rotaru, V., Huang, Y., Li, T., Evans, J. & Chattopadhyay, I. Event-level prediction of urban crime reveals a signature of enforcement bias in US cities. *Nat. Hum. Behav.* **6**(8), 1056–1068 (2022). https://doi.org/10.1038/s41562-022-01372-0. O resumo veio da Europe PMC (PMID 35773401). A ficha do parecer está correta.

**O que estudou e achou.** Propõem um algoritmo de inferência estocástica que aprende dependências espaço-temporais a partir de registros de eventos. A AUC média fica em torno de 90% para crimes previstos por semana, em células de cerca de 1.000 pés, em Chicago. Perturbações do modelo sugerem que a resposta policial ao aumento do crime é enviesada pelo nível socioeconômico do bairro, em oito cidades dos EUA.

**Com que conversa.**
- Com "Monthly forecasts add little to a stable map of past crime".
- Com o parágrafo de riscos ("flags can feed back into where police look{lum2016}").

**Ameaça à originalidade?** Não diretamente. Lida apressadamente, porém, uma AUC alta pode parecer contradizer "too sparse to … forecast".

**Por que não citar.** Alvo, escala e métrica são outros, e o viés que estudam (da resposta policial) não é o do manuscrito (notificação desigual pelas vítimas e realimentação dos alertas), que já tem `akpinar2021`, `builgil2021` e `lum2016`. Entraria pelo prestígio da revista, o que o R18 pede para evitar.

**Para a resposta aos revisores (interpretação minha, não achado de Rotaru et al.).** Uma AUC calculada entre células e semanas premia sobretudo o ordenamento espacial estável. Esse é o componente que o manuscrito também acha previsível (R² = 0,80 de um teto de 0,92 entre e dentro dos setores). O componente que não é capturado é a variação dentro do setor.

### S20. Varese & Zeng (2024) — **não citar**

**Ficha:** Varese, F. & Zeng, F. The relationship between social order and crime in Nottingham, England. *Nat. Cities* **1**(12), 821–829 (2024). Online em 1 nov. 2024. https://doi.org/10.1038/s44284-024-00161-2. O parecer omitia autores, volume e páginas.

**O que estudou e achou.** Combinam entrevistas com uma base de chamadas do público à polícia de Nottingham (2012–2019). Identificam um grupo de crime organizado do tipo governança num bairro (Bestwood) e o comparam com o bairro mais parecido (Bulwell): alguns crimes comuns são menos frequentes no primeiro. Concluem que a governança criminal pode surgir num país com alta capacidade de policiamento.

**Com que conversa.** Só indiretamente, com "Candidates include … territorial control by organized crime{biderman2019}", na seção do efeito persistente.

**Ameaça?** Nenhuma.

**Por que não citar.** O ponto já está coberto, para São Paulo, por `biderman2019` (PCC e homicídios). O valor de S20 é editorial, porque mostra que um estudo de uma cidade só cabe na Nature Cities, e isso não pede citação. Só faria sentido se o texto desenvolvesse a governança criminal como candidata ao estado.

### S21. De Nadai et al. (2020) — **citar**

**Ficha:** De Nadai, M., Xu, Y., Letouzé, E., González, M. C. & Lepri, B. Socio-economic, built environment, and mobility conditions associated with crime: a study of multiple cities. *Sci. Rep.* **10**, 13871 (2020). https://doi.org/10.1038/s41598-020-70808-2. O parecer omitia os autores.

**O que estudou e achou.** Um modelo bayesiano relaciona crimes violentos e contra o patrimônio, em pequenas áreas, a fatores socioeconômicos, ao ambiente construído (incluindo uso do solo) e à mobilidade medida por telefonia móvel, em Boston, Bogotá, Los Angeles e Chicago. A combinação dos três grupos explica o crime melhor do que as abordagens tradicionais. Os mesmos fatores, porém, se relacionam com o crime de modo muito diferente de uma cidade para outra; os autores concluem que não existe um modelo que sirva para todas.

**Com que conversa.**
- Com "Some of these results should travel and some should not. … The profiles and rhythms are specific to São Paulo".
- Com o uso de ambiente construído e mobilidade como covariáveis, que é a alternativa à atribuição por composição.

**Ameaça à originalidade?** Não. É regressão sobre covariáveis, sem exposições conhecidas, sem 15 tipos e sem hora. Ajuda a mostrar o que a atribuição acrescenta: taxas por unidade de exposição numa partição exaustiva da cidade.

**Frase proposta (Discussão):**
> The profiles and rhythms are specific to São Paulo, and associations of crime with the built environment and mobility differ between cities{denadai2020}, but the method needs only a cadastre, …

---

## 2. Busca complementar (OpenAlex)

**Buscas feitas (`search=`):**
- uso do solo e taxas: "crime rates by land use type ecological inference areal counts", "land use specific crime rates Poisson regression area of land use", "crime attractors generators detractors land use", "crime per land use parcel exposure rate", "attributing crime to land use parcels within areal units", "crime rate per facility type exposure denominator", "ecological inference crime";
- perfis multicrime: "crime type specific associations land use multiple crime types facilities", "location quotient crime specialization land use", "crime-general and crime-specific spatial patterns multivariate", "mixed land use neighborhood crime types";
- hora: "time of day land use crime street robbery hourly", "temporal typology of crime places hour";
- previsibilidade e ruído: "limits of predictability crime forecasting", "predictability of crime entropy spatiotemporal", "early warning system temporary crime hot spots chronic", "reducing bias law of crime concentration Poisson", "marginal crime concentration", "more places than crimes", "overdispersion crime counts small areas month Poisson noise".

**Veredito sobre as afirmações de originalidade.**
- **"Few studies read the full composition of a city, all its crime types and the hour together" se sustenta.** Nenhum trabalho encontrado faz as três coisas com composição exaustiva e sem coordenadas. O mais próximo é Matijošaitienė et al. 2019 (uso do solo por lote × hora × três crimes, em Manhattan), que confirma o "few" e desaconselha escrever "first".
- **"Facility and land-use studies estimate these effects for a few uses or crime types at a time" está exposta.** Stucky & Ottensmann 2009 usam 30 categorias de uso do solo, e Sypion-Dutkowska & Leitner 2017 cruzam muitos usos com 9 tipos de crime. A correção proposta está no item (b) abaixo.
- **"Monthly forecasts add little to a stable map of past crime" tem antecedente direto** em Gorr & Lee 2015, item (a).
- **O argumento do ruído tem antecedente criminológico** na medição da concentração com dados esparsos, item (c).

### (a) Gorr & Lee (2015) — **citar** (prioridade mais alta)

**Ficha:** Gorr, W. L. & Lee, Y. Early warning system for temporary crime hot spots. *J. Quant. Criminol.* **31**(1), 25–47 (2015). Online em 25 mar. 2014. https://doi.org/10.1007/s10940-014-9223-8.

**Resumo.** A Crossref, o OpenAlex e a Semantic Scholar não trazem o resumo da versão publicada; li o do working paper homônimo no Figshare da CMU (2013, doi:10.1184/r1/6471302). Com crimes violentos de Pittsburgh (2000–2010), comparam a alocação constante em hot spots crônicos com um sistema de alerta precoce que liga e desliga a alocação nos surtos. Mesmo os hot spots mais quentes alternam meses "ligados" e "desligados", mas as duas estratégias têm eficiência quase igual. Regras simples de alocação dinâmica não melhoram a eficiência. Os hot spots crônicos ficam perto do comércio; os dinâmicos são mais residenciais e dispersos.

**Com que conversa.**
- Discussão: "Monthly forecasts add little to a stable map of past crime, so most of the value of predictive policing{mohler2015} lies in that map."
- Resultados: "real month-to-month variation exists, but the models do not capture it".

**Ameaça?** Sim, à novidade da mensagem: o "mapa estável" já foi documentado como estratégia de alocação. O teto de ruído é a formalização desse resultado, não um fenômeno novo (o revisor de domínio já apontava isso em `review/r2_dominio.md`, W6). Citar protege o texto.

**Frase proposta (Discussão, logo após a frase acima):**
> In Pittsburgh, early-warning deployment to flaring hot spots was no more efficient than steady deployment to chronic ones{gorr2015}.

**Antes de citar:** confirmar no resumo da versão publicada na JQC que o achado se manteve.

### (b) Stucky & Ottensmann (2009) — **trocar por `andresen2017`** (saldo zero)

**Ficha:** Stucky, T. D. & Ottensmann, J. R. Land use and violent crime. *Criminology* **47**(4), 1223–1264 (2009). https://doi.org/10.1111/j.1745-9125.2009.00174.x. A Crossref traz o título em caixa alta, com asterisco.

**Resumo.** Usam crimes violentos geocodificados de Indianápolis, 30 categorias de uso do solo e o Censo de 2000, em células de 1.000 × 1.000 pés, com regressão binomial negativa. Usos específicos predizem as contagens de crimes violentos individuais e agregados, uns para mais e outros para menos, e alguns usos condicionam o efeito da desvantagem socioeconômica.

**Com que conversa.** Com "Facility and land-use studies estimate these effects for a few uses or crime types at a time{twinam2017,andresen2017}". É o antecedente mais próximo de (a): efeitos do uso do solo estimados a partir de contagens por área, mas com os usos como covariáveis log-lineares, não como taxas aditivas por unidade de exposição.

**Ameaça?** Sim, à palavra "few uses": são 30 categorias. Sypion-Dutkowska & Leitner 2017 (abaixo) cruzam muitos usos com 9 tipos de crime. A diferença real do manuscrito é outra: taxas aditivas por unidade de exposição, numa partição exaustiva da cidade, para 15 tipos e por hora, sem coordenadas.

**Observação sobre `andresen2017`.** Pelo título ("The trajectories of crime at places: understanding the patterns of disaggregated crime types", *J. Quant. Criminol.* 33, 427–449), não é um estudo de efeito de facilidades ou de uso do solo. Não consegui ler o resumo por API. O revisor simulado de domínio (`review/r2_dominio.md`, W10, "verified at abstract level") descreve a obra como trajetórias de oito tipos de crime em segmentos e interseções de Vancouver, o que confirma que a citação está mal colocada nessa frase. Os autores devem conferir.

**Frase proposta (introdução):**
> Facility and land-use studies relate crime counts to uses as covariates, mostly for a few uses or crime types at a time{stucky2009,twinam2017}, …

**Sobre `twinam2017`.** Também não li o resumo dela. O mesmo W10 a descreve como o efeito de usos comerciais e mistos sobre o crime no entorno, em Chicago. Se for isso, ela cabe em "a few uses … as covariates". Os autores devem confirmar.

**Alternativa:** `kinney2008` (já está no dicionário DOI, sem citação). Kinney et al. analisam agressão e furto de veículo em mais de 60 mil lotes de uma cidade da Colúmbia Britânica, com geradores e atratores. Serve para "a few crime types", mas não para contagens por área.

### (c) Bernasco & Steenbeek (2017) — **citar**

**Ficha:** Bernasco, W. & Steenbeek, W. More places than crimes: implications for evaluating the law of crime concentration at place. *J. Quant. Criminol.* **33**(3), 451–467 (2017). Online em 20 set. 2016. https://doi.org/10.1007/s10940-016-9324-7.

**Resumo.** Propõem versões generalizadas da curva de Lorenz e do índice de Gini que comparam a concentração observada com a máxima igualdade possível dados os eventos, e não com a igualdade perfeita. Isso corrige o viés quando há menos crimes do que lugares. A demonstração usa dois tipos de crime em Haia.

**Com que conversa.** Resultados: "Month-to-month variation is thus consistent with a property shared by all tracts that only high-count tracts make visible, much as Poisson measurement noise masks variation in expression at low counts in single cells{sarkar2021}." Hoje o argumento do ruído se apoia só na biologia (`sarkar2021`) e em Cochran. O revisor de domínio pediu a ancoragem criminológica.

**Ameaça?** Parcial. O problema geral (esparsidade que distorce medidas) é conhecido entre lugares. O teto de ruído o leva ao tempo e ao R² de previsão, e essa extensão é a contribuição do manuscrito.

**Frase proposta:**
> …much as Poisson measurement noise masks variation in expression at low counts in single cells{sarkar2021} and sparse counts bias measures of crime concentration across places{bernascosteenbeek2017}.

**Alternativas verificadas:**
- Chalfin, Kaplan & Cuellar 2021, *J. Res. Crime Delinq.* **58**(4), 467–504, doi:10.1177/0022427820984213. Comparam a concentração observada com uma distribuição contrafactual de crimes sorteados entre segmentos; a concentração substantiva é menor do que a literatura relata. É redundante com Bernasco & Steenbeek.
- Mohler et al. 2019, *J. Quant. Criminol.* **35**(4), 747–765, doi:10.1007/s10940-019-09404-1. Metadados conferidos, mas **resumo não verificado**; não recomendo.

### (d) Quick, Li & Brunton-Smith (2018) — citar **só em Methods** (não conta)

**Ficha:** Quick, M., Li, G. & Brunton-Smith, I. Crime-general and crime-specific spatial patterns: a multivariate spatial analysis of four crime types at the small-area scale. *J. Crim. Justice* **58**, 22–32 (2018). https://doi.org/10.1016/j.jcrimjus.2018.06.003. O resumo veio da Semantic Scholar.

**Resumo.** Modelos espaciais bayesianos multivariados aplicados a arrombamento, roubo, crimes de veículo e violência, em pequenas áreas. A variabilidade residual se divide em componentes compartilhados e específicos. Dois componentes compartilhados aparecem, um geral e um dos crimes de furto, e explicam a maior parte da variabilidade.

**Com que conversa.** Com os "programs" da NMF ("Factorizing the tract-by-crime matrix{kotliar2019} gave four programs…"). É o equivalente criminológico dos programas e mostra que a estrutura compartilhada entre crimes já foi estimada.

**Frase proposta (Methods, "Crime types and profiles"):**
> Programs came from non-negative matrix factorization of the tract-by-type matrix scaled by type means{kotliar2019}, a non-negative counterpart of the shared components of multivariate crime models{quick2018}, …

Se houver vaga no texto principal, a mesma ressalva cabe na frase dos programas em Resultados.

### (e) Andresen (2007) — citar **só em Methods** (não conta)

**Ficha:** Andresen, M. A. Location quotients, ambient populations, and the spatial analysis of crime in Vancouver, Canada. *Environ. Plan. A* **39**(10), 2423–2444 (2007). https://doi.org/10.1068/a38187.

**Resumo.** Introduz o quociente de localização em criminologia para medir a especialização do crime (furto de veículo, arrombamento e violência) em Vancouver. As teorias de desorganização social e de atividades rotineiras predizem a especialização quando lidas como atratores específicos de cada crime.

**Com que conversa.** Com o enriquecimento dos perfis ("enrichment is the log₂ ratio of this share to its mean over crime types"), que é parente do quociente de localização. Difere num ponto: compara com a média não ponderada entre tipos, e não com a participação da classe em todo o crime. Um criminologista vai reconhecer a medida.

**Frase proposta (Methods):**
> …and enrichment is the log₂ ratio of this share to its mean over crime types, akin to a location quotient of crime{andresen2007}.

### (f) Opcionais (só com corte extra, ver seção 3)

**Ceccato & Moreira (2021).** *The dynamics of thefts and robberies in São Paulo's metro, Brazil.* *Eur. J. Crim. Policy Res.* **27**(3), 353–373 (2021); online em 25 ago. 2020. https://doi.org/10.1007/s10610-020-09462-3.
- Achados: no metrô de São Paulo (2010–2017), os furtos ocorrem mais dentro das estações e os roubos fora. O crime se concentra em poucas estações centrais e terminais e varia com o local e a hora.
- Conversa com "and phone theft at rail stations (+1.6; not tested at finer scale)". É corroboração local de um resultado que o manuscrito não testa em escala fina, e responde à falta de literatura paulistana apontada pelo revisor de domínio (W15).
- Frase: "(+1.6; not tested at finer scale, but thefts in São Paulo's metro occur mostly inside stations{ceccato2021})".

**Hipp & Kim (2019).** *Explaining the temporal and spatial dimensions of robbery: differences across measures of the physical and social environment.* *J. Crim. Justice* **60**, 1–12 (2019). https://doi.org/10.1016/j.jcrimjus.2018.10.005. O resumo completo veio da versão no eScholarship, via OpenAlex.
- Achados: em segmentos de rua do sul da Califórnia, as relações com o roubo mudam com a hora. Varejo e restaurantes no entorno elevam o risco da tarde até a noite; o emprego reduz o risco de dia, mas não à noite.
- Conversa com "Robbery on retail, high-rise and service parcels peaks between 19:00 and 22:00". É também a evidência mais direta, para a hora, na lista do "mixed".
- Frase: "…peaks between 19:00 and 22:00, as robbery risk near retail and restaurants rises into the evening in Southern California{hippkim2019}".
- Ressalva: o roubo é exploratório (P = 0,07 em 2025), então a prioridade é baixa.

### (g) Verificados e não recomendados

| Obra (DOI) | Por que não |
|---|---|
| Matijošaitienė, I., Zhao, P., Jaume, S. & Gilkey, J. Prediction of hourly effect of land use on crime. *ISPRS Int. J. Geo-Inf.* 8, 16 (2019), 10.3390/ijgi8010016 | Uso do solo por lote × hora × três crimes (Manhattan), com aprendizado de máquina. É o mais próximo da tríade, mas confirma o "few" e não exige citação. Desaconselha escrever "first". |
| Sypion-Dutkowska, N. & Leitner, M. Land use influencing the spatial distribution of urban crime: a case study of Szczecin, Poland. *ISPRS Int. J. Geo-Inf.* 6, 74 (2017), 10.3390/ijgi6030074 | Muitos usos × 9 crimes, com buffers e quociente de localização, eventos geocodificados. Motiva o "mostly" na frase da introdução; Stucky & Ottensmann cobre o ponto numa revista central. |
| Corcoran, J., Zahnow, R., Kimpton, A., Wickes, R. & Brunsdon, C. The temporality of place: constructing a temporal typology of crime in commercial precincts. *Environ. Plan. B* 48, 9–24 (2021), 10.1177/2399808319846904 | Tipologia temporal de 2.286 polos comerciais em Queensland. Parente do relógio, mas só para o comércio e com outro desenho. |
| O'Brien, D. T., Ristea, A., Hangen, F. & Tucker, R. Different places, different problems: profiles of crime and disorder at residential parcels. *Crime Sci.* 11, 4 (2022), 10.1186/s40163-022-00165-0 | Tipologia de lotes residenciais de Boston definida *pelo* crime e pela desordem (k-means). O manuscrito tipa os lotes sem crime e depois atribui. Útil numa resposta a revisor, não no texto. |
| Prieto Curiel, R. Weekly crime concentration. *J. Quant. Criminol.* 39, 97–124 (2023), 10.1007/s10940-021-09533-6 | Concentração temporal semanal por tipo de crime na Cidade do México. Tangente ao relógio. |
| Amram, S., Weisburd, D. & Shay, M. *Int. Ann. Criminol.* 62, 8–29 (2024), 10.1017/cri.2024.1 | Crime geral × específico em segmentos de Tel Aviv-Yafo. Redundante com Quick et al. 2018. |

---

## 3. O que sai do texto principal para manter cerca de 50

**Critério.** Saem primeiro as referências técnicas cujo papel no texto principal é rotular um método, que já estão citadas em Methods ou podem entrar lá. Como as referências só de Methods não contam, nenhuma obra desaparece do artigo. No texto principal, o sobrescrito vira "(Methods)".

| Chave | Frase atual no texto principal | Papel | Já está em Methods? | Ação |
|---|---|---|---|---|
| `traag2019` | "Clustering these attributes with the Leiden algorithm{traag2019}" | rótulo de algoritmo | sim ("Parcel types…") | trocar por "(Methods)" |
| `gneiting2007` | "improved the continuous ranked probability score{gneiting2007}" | definição de escore | sim ("Forecasting benchmark") | trocar por "(CRPS; Methods)" |
| `cochran1954` | "given Poisson noise{cochran1954} (Methods)" | teste de dispersão | sim ("Noise ceiling and dispersion") | tirar o sobrescrito; o "(Methods)" já está na frase |
| `callaway2021` | "in a staggered event study{callaway2021}" | estimador | sim ("in the spirit of ref.") | sai com R6: o estudo de evento vai para o Extended Data com uma frase, e o estimador não é exatamente o de Callaway–Sant'Anna (plano, R6) |
| `gale2016` | "a geodemographic k-means baseline{gale2016}" | baseline técnico | **não** | mover para Methods, "Parcel types…": "…and compared with a geodemographic k-means baseline{gale2016} by ARI" |
| `metro2017` | "Origin–Destination household survey{metro2017}" | fonte de dados | sim ("Data") e em Data availability | trocar por "(Methods)" |
| `andresen2017` | "…at a time{twinam2017,andresen2017}" | exemplo de estudo de uso do solo, aparentemente mal colocado | não | sai, trocada por `stucky2009` |

**Se só parte das inclusões for aceita,** migrar na ordem da tabela: `traag2019`, `gneiting2007`, `cochran1954` e `callaway2021` primeiro, porque não exigem nenhuma mudança em Methods.

**Se os opcionais (f) entrarem,** cada um pede um corte a mais. Os candidatos menos custosos são estes, com cautela:
- `hollispeel2011`: revisão sobre vigilância; `cohen1979` já introduz os guardiões capazes.
- `shaw1942` ou `park1925`: as duas sustentam a mesma frase sobre a Escola de Chicago.

Não recomendo cortar referências conceituais para abrir espaço para os opcionais.

---

## 4. Linhas prontas para `paper/build.py`

### `DOI`

```python
    # recomendadas, texto principal
    "quick2019": "10.1177/2399808317744779",
    "wu2022": "10.1140/epjds/s13688-022-00366-2",
    "alborszumel2026": "10.1007/s10940-025-09629-3",
    "denadai2020": "10.1038/s41598-020-70808-2",
    "gorr2015": "10.1007/s10940-014-9223-8",
    "bernascosteenbeek2017": "10.1007/s10940-016-9324-7",
    "stucky2009": "10.1111/j.1745-9125.2009.00174.x",
    # recomendadas, só Methods
    "quick2018": "10.1016/j.jcrimjus.2018.06.003",
    "andresen2007": "10.1068/a38187",
    # opcionais
    "ceccato2021": "10.1007/s10610-020-09462-3",
    "hippkim2019": "10.1016/j.jcrimjus.2018.10.005",
```

**Ano impresso.** O `build.py` usa `published-print` antes de `published-online`, então sai 2019 para Quick et al. 2019, 2026 para Albors Zumel, 2015 para Gorr & Lee, 2017 para Bernasco & Steenbeek e 2021 para Ceccato & Moreira. As chaves seguem esse ano. `wu2022` e `denadai2020` só têm data online, que coincide com o ano.

### `TITULOS`

Só onde `frase()` erra, o que testei rodando a função do próprio `build.py`:

```python
    "stucky2009": "Land use and violent crime",                       # Crossref: "LAND USE AND VIOLENT CRIME*"
    "andresen2007": "Location quotients, ambient populations, and the spatial analysis of crime in Vancouver, Canada",  # frase() gera "canada"
    "ceccato2021": "The dynamics of thefts and robberies in São Paulo’s metro, Brazil",  # frase() gera "São paulo’s"
```

**Títulos que `frase()` já converte certo** (para conferência):
- quick2019: "Time-varying relationships between land use and crime: a spatio-temporal analysis of small-area seasonal property crime trends"
- wu2022: "Enhancing short-term crime prediction with human mobility flows and deep learning architectures"
- alborszumel2026: "Deep learning for crime forecasting: the role of mobility at fine-grained spatiotemporal scales"
- denadai2020: "Socio-economic, built environment, and mobility conditions associated with crime: a study of multiple cities"
- gorr2015: "Early warning system for temporary crime hot spots"
- bernascosteenbeek2017: "More places than crimes: implications for evaluating the law of crime concentration at place"
- quick2018: "Crime-general and crime-specific spatial patterns: a multivariate spatial analysis of four crime types at the small-area scale"
- hippkim2019: "Explaining the temporal and spatial dimensions of robbery: differences across measures of the physical and social environment"

Se um dia S20 entrar: `"varese2024": "The relationship between social order and crime in Nottingham, England"`, porque `frase()` gera "nottingham".

### `ABREV`

Só uma revista falta:

```python
    "EPJ Data Science": "EPJ Data Sci.",
```

As demais já estão no dicionário: *J. Quant. Criminol.*, *Environ. Plan. B Urban Anal. City Sci.*, *Sci. Rep.*, *Criminology*, *J. Crim. Justice*, *Environ. Plan. A*, *Eur. J. Crim. Policy Res.* Se S19 ou S20 entrarem: `"Nature Human Behaviour": "Nat. Hum. Behav."` e `"Nature Cities": "Nat. Cities"`.

### Acentos de Wu et al. (cosmético)

A Crossref grafa "Frias-Martinez". Para "Frías-Martínez", o único caminho no `build.py` é o `EXTRA` com `authors`, que dispensa a Crossref e exige todos os campos:

```python
    "wu2022": {"authors": [("Wu", "J."), ("Abrar", "S. M."), ("Awasthi", "N."), ("Frías-Martínez", "E."), ("Frías-Martínez", "V.")],
               "title": "Enhancing short-term crime prediction with human mobility flows and deep learning architectures",
               "container": "EPJ Data Science", "volume": "11", "page": "53", "year": 2022},
```

---

## 5. Limites da verificação

- **Gorr & Lee 2015:** o resumo lido é o do working paper de 2013 no Figshare da CMU, de título ligeiramente diferente. Confirmar no resumo da versão da JQC antes de citar.
- **Resumos não obtidos por API:** `andresen2017`, `twinam2017` e Mohler et al. 2019. Para as duas primeiras, a única descrição disponível é a do revisor simulado de domínio (W10), que é fonte secundária. A Springer e a Elsevier ocultam os resumos, e a página da Springer devolveu um desafio anti-robô. Por isso:
  - a observação de que `andresen2017` está mal colocada se apoia só no título;
  - Mohler et al. 2019 não é recomendado.
- **Quick, Law & Li 2019:** não confirmei a cidade estudada, que o resumo não nomeia.
- **Wu et al. 2022:** o resumo não nomeia as cidades; a frase proposta não as cita.
- A Semantic Scholar limitou as requisições (erro 429) em várias tentativas.
- A busca no OpenAlex foi curta, de propósito, como o pedido estabelecia. Não é uma revisão sistemática.
