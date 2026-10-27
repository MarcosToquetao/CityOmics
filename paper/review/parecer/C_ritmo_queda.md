# Agente C: ritmo, denominador de pedestres, queda, evento-estudo e benchmark

**Itens:** R5 (parcial), R6, R11, R13, R14, permutação em blocos do relógio, intervalos do perfil horário e da razão fim de semana/dia útil.

**Escopo:** só os 77 distritos de exploração e só 2022–2025 (todo caminho passa por `guard.pre2026`). Sem rede e sem commit. Nenhum arquivo existente foi editado.

**Números:** todos saem de `data/processed/atlas/fenotipo/ritmo_queda.json`, exceto os da Tabela S1, que saem do código lido. Para validar o módulo, refiz com a mesma matriz E os números publicados: ρ = 0,752, risco às 3h de 19,0×, r mediano 0,030 e os P do relógio (0,005; 0,07; 0,005; 0,005). Todos batem.

**Dados geocodificados (confirmando o Agente A):** o relógio, o risco por pedestre e o evento-estudo usam só eventos geocodificados. Em `eventos_multi_atribuidos.parquet`, todo evento com `cd_setor` tem coordenada válida (`via = coord`): são 263.935 eventos de celular em 2024–2025 na cidade. Os 56.975 sem coordenada (via bairro, DP ou nenhuma) não têm setor. `fenotipo._eventos_relogio` e `presenca._crime` exigem `cd_setor`, e o evento-estudo filtra `coord_valida`.

---

## 0. Achado colateral grave: o setor dos segmentos de rua está trocado em `ruas.parquet`

Isto afeta a matriz de exposição E de todo o atlas, não só as minhas análises.

**O que acontece:** em `atlas/streets.segments`, o `reset_index()` roda antes do `drop_duplicates`. Depois, `pts = GeoDataFrame({"i": np.arange(len(e))}, geometry=mid)` alinha a geometria pelo rótulo do índice. Com isso, a linha k recebe o ponto médio de outra aresta, ou nenhum. Reproduzi o mecanismo num exemplo mínimo (geopandas 1.2.0). A geometria, a classe e o comprimento de cada linha estão certos; só `cd_setor` está trocado.

**Medidas** (`ritmo_queda.json → ruas_setor.diagnostico`):
- só 0,2% dos 179.496 segmentos têm o `cd_setor` igual ao setor do próprio ponto médio, e só 1,6% caem no distrito certo;
- 33% dos segmentos ficaram sem setor;
- o comprimento de rua por setor em `setor_ruas_estacoes.parquet` tem 8.311 km de vias locais, contra 12.528 km corretos (arteriais 1.318 contra 1.812; coletoras 1.905 contra 2.781);
- a correlação de Pearson entre a exposição gravada e a correta é de 0,31 a 0,51, conforme a classe.

**Consequências que medi** (só pontos; E corrigida = as três colunas de rua refeitas pelo ponto médio):

| Quantidade | E do artigo | E corrigida |
|---|---|---|
| D² do celular 2025 | 0,338 | 0,450 |
| λ comércio de rua médio (/km) | 70,5 | 55,8 |
| λ estação de trilho | 87,0 | 74,2 |
| λ terminal | 71,5 | 56,3 |
| λ arterial / coletora / local (/km) | 4,6 / 2,4 / 1,4 | 14,6 / 6,4 / 1,0 |
| ρ entre as classes, λ com e sem correção | — | 0,947 |
| ρ km × pedestre (só a pé, σ = 300 m) | 0,752 | 0,583 |
| r mediano roubo × pedestres | 0,030 | 0,027 |
| Fração 04–06h do popular (modelo) | 0,412 | 0,356 |
| Razão fim de semana/dia útil, roubo, popular | 0,40 | 0,41 |
| P do relógio, roubo 2025 (nulo individual) | 0,07 | 0,015 |
| H do relógio, furto 2024 / 2025 | 0,114 / 0,073 | 0,137 / 0,094 |
| Razão relativa de queda do roubo: popular, esquina, comércio médio, trilho, rua local | 0,56; 0,49; 1,15; 0,91; 0,89 | 0,57; 0,29; 1,11; 0,83; 0,99 |

**Evento-estudo publicado:** o filtro de exploração e as células distrito × classe usam o `cd_setor` trocado. Dos 158.663 segmentos do conjunto publicado, 20,3% (32.183) estão fisicamente em distritos do cofre. Os segmentos sem setor entraram como "exploração" porque `"nan"` não está no cofre. Com isso, entraram no evento-estudo 239.506 eventos de crime de rua de distritos do cofre. A frase de Methods "No crime result of the atlas has been computed in the vault districts" não vale para o evento-estudo publicado. O resultado é um efeito nulo agregado e não toca C1–C5, mas o fato deve ser registrado. Refiz o evento-estudo com o setor correto (seção 5).

**Não afetados:** a validação pontual (`attribution.point_validation`) liga eventos a segmentos pela geometria, então só se acerta indiretamente. As contagens de estações vêm de outro `sjoin` e estão certas.

**Recomendação (para o coordenador; eu não editei):**
1. corrigir `streets.segments` montando os pontos com `geometry=mid.values` ou fazendo `reset_index` depois do `drop_duplicates`;
2. refazer `ruas.parquet`, `setor_ruas_estacoes.parquet` e `setor_composicao_2025.parquet`;
3. rodar de novo o atlas e o evento-estudo. Os números dos Agentes A e B que usam E também mudam.

`ritmo_queda.ruas_setor_correto()` e `setor_exposicao_corrigida()` fazem a correção sem tocar nos arquivos.

---

## 1. Denominador de pedestres (R5)

**Pergunta:** o que a OD mede, e o pico de 19× às 3h é estável?

**Método:**
- TIPVG conferido no `LAYOUT OD2017_v1.xlsx`: 1 coletivo, 2 individual, 3 a pé, 4 bicicleta (MODO 15 bicicleta, 16 a pé).
- Variante "só a pé": nas viagens de bicicleta ficam só ANDA_O e ANDA_D.
- Bootstrap da amostra da OD por domicílio, reamostrado com reposição dentro da zona (n_z sorteios em cada uma das 492 zonas com domicílios; 26.110 domicílios com viagem). A zona é o estrato do desenho: toda zona é amostrada e os fatores de expansão são calibrados por zona. Reamostrar zonas inteiras trataria estratos como conglomerados sorteados, apagaria pedestres de áreas inteiras e superestimaria a variância.
- B = 500 em σ = 300 m e 200 em σ = 150 e 600 m. Mais um bootstrap conjunto (B = 200), que sorteia também os distritos do crime.

**Resultados:**
- A bicicleta responde por 2,0% das pessoas-hora na rua nos setores de exploração: 2,2% às 3h, no máximo 6,7% à 1h. Com só a pé, os pontos ficam iguais: ρ = 0,752, pico às 3h de 18,98×, r mediano 0,030.
- **O pico noturno é real, mas a altura e a hora são instáveis.** Às 3h, o denominador se apoia em 149 trechos a pé da amostra (viagens a pé ou pontas de outras viagens) de 85 domicílios (n efetivo de Kish ≈ 29), contra 17.267 às 18h.

| Só a pé | Ponto | IC 95%, OD (B = 500) | IC 95%, OD + distritos (B = 200) |
|---|---|---|---|
| Risco às 3h (× média diária) | 19,0 | 13,4–29,9 | 11,7–38,6 |
| Hora do pico (frequência nas réplicas) | 3h | 3h 69%, 2h 26%, 1h 5% | 3h 63%, 2h 30%, 1h 8% |
| ρ km × pedestre | 0,75 | 0,73–0,78 | 0,58–0,85 |
| r mediano roubo × pedestres | 0,030 | 0,018–0,042 | −0,01 a 0,12 |

- **Sensibilidade a σ** (150 / 300 / 600 m):
  - risco às 3h: 17,8 / 19,0 / 20,6;
  - ρ: 0,67 / 0,75 / 0,79 (IC OD 0,59–0,72 com σ = 150 e 0,78–0,83 com σ = 600);
  - r mediano: 0,028 / 0,030 / 0,034.
- **Divergência entre código e Methods.** O código divide pela soma das densidades por setor (pessoas/km²), não pelo total de pessoas. Com o total de pessoas, o risco às 3h é 18,0 (IC 12,5–28,5), e a hora do pico fica dividida entre 3h (51%) e 2h (43%).
- Com a exposição de ruas corrigida (seção 0), ρ cai para 0,58.

**Implicação:**
- O risco por pedestre na madrugada é muito alto em todas as réplicas: o pico fica entre 1h e 3h e sempre acima de 13×.
- "03:00" e "19 times" são pontos de uma razão com denominador pequeno: precisam de intervalo, e a hora deve virar uma faixa.
- "Pedestrians" é defensável se o Methods excluir a bicicleta.
- Os números de ρ só ficam firmes depois de corrigir E.

**Frases propostas:**
- Methods: "…walking trips counted entirely as time on the street (cycling, 2% of street person-hours, was excluded), … and summed per tract and hour for weekdays; the citywide risk divides weekday robberies by the summed pedestrian density of tracts."
- Results: "…and citywide robbery risk per pedestrian is highest between 01:00 and 03:00, about 19 times its daily mean at 03:00 (95% interval 13–30 from resampling survey households within zones; Fig. 4c), a ratio that rests on few respondents outside at that hour."
- Results: "Across classes, the median correlation between the hourly profiles of robbery and of pedestrians is 0.03 (95% interval 0.02–0.04)."

---

## 2. Relógio: permutação em blocos

**Pergunta:** o P ≤ 0,005 sobrevive quando eventos agrupados no tempo deixam de ser trocados um a um?

**Método:**
- Bloco = todos os eventos do mesmo setor, no mesmo dia (ou mês) e no mesmo período. O rótulo de período do bloco troca com o de outro bloco do mesmo tamanho no mesmo distrito.
- Isso preserva exatamente os eventos por setor e por distrito × período (teste sintético) e mantém juntos os eventos de um mesmo episódio. Um assalto com várias vítimas fica no bloco do dia; uma sequência de semanas fica no bloco do mês.
- Blocos sem par de tamanho ficam fixos, o que deixa o teste conservador: no máximo 1,3% dos eventos de roubo e 5,6% dos de furto.
- 999 permutações por nulo; o nulo do artigo foi reproduzido com 200 e semente 0.

**Resultados (P):**

| Desfecho, ano | Eventos | Artigo (individual) | Blocos de dia | Blocos de mês | Eventos em blocos > 1 (dia / mês) |
|---|---|---|---|---|---|
| Furto 2024 | 55.830 | 0,005 | 0,001 | 0,001 | 15% / 50% |
| Furto 2025 | 61.594 | 0,005 | 0,001 | 0,001 | 15% / 51% |
| Roubo 2024 | 46.141 | 0,005 | 0,002 | 0,005 | 9% / 29% |
| Roubo 2025 | 38.412 | 0,070 | 0,152 | 0,459 | 8% / 28% |

O agrupamento existe: no furto de 2024, a mediana do H nulo sobe de 0,025 para 0,051 com blocos de dia e 0,069 com blocos de mês. Ainda assim, o furto fica muito acima de qualquer nulo (H = 0,114 e 0,073). O roubo de 2025 se afasta mais do limiar. Com E corrigida, o P individual do roubo de 2025 é 0,015 (seção 0); o nulo em blocos não foi refeito com E corrigida.

**Implicação:** o teste pré-especificado (furto) está sustentado. O roubo de 2025 fica mais fraco.

**Frases propostas:**
- Results: "For phone theft, the pre-specified test, class-specific departures exceeded the null in 2024 and 2025 (P ≤ 0.005), also under block permutations that keep together events of the same tract, day or month and period (P ≤ 0.001)… Phone robbery departed from the null in 2024 (P ≤ 0.005) but not in 2025 (P = 0.07; 0.15 and 0.46 under block permutations)."
- Methods: "A block null permuted period labels among equal-sized blocks within districts, a block being the events of one tract on one day (or in one month) in one period (999 permutations)."
- Limitações: remover "block permutations for the clock" da lista de pendências.

---

## 3. Intervalos do relógio

**Pergunta:** quanto do pico pré-amanhecer e da razão de fim de semana é incerteza, e o modelo bate com a contagem sem modelo?

**Método:**
- Bootstrap de distritos, B = 200.
- Roubo em dias úteis com hora exata, 2024–2025 (53.912 eventos).
- Setores dominados = classe com ≥ 50% do roubo esperado, mesma definição de `robustez.relogio_bruto`: 313 setores para o popular, 5.679 para o comércio.
- Além da contagem observada, calculei a fração prevista pelo próprio modelo nos mesmos setores.

**Resultados:**
- **04–06h no popular:**
  - parte da classe no modelo: 41% (IC 31–52%);
  - nos 313 setores dominados, o modelo prevê 30% (24–36%), e o observado é 16%. Com bootstrap de distritos, o IC do observado é 9–23%, mais largo que o 12–21% de eventos citado no artigo;
  - nos setores de comércio, previsto 6,1% (5,1–7,5%) e observado 6,0% (5,0–7,5%).
  - Ou seja, o modelo erra justamente onde pode ser checado: superestima o pré-amanhecer do popular cerca de duas vezes.
- **Fim de semana/dia útil das taxas diárias (Fig. 4e):**
  - roubo de celular no popular: 0,40 (IC 0,19–0,76);
  - sem modelo, nos setores dominados pelo popular (416 eventos): 0,83 (0,64–1,11);
  - roubo de outros bens no popular: 0,37 (0,18–0,54), contra 0,77 (0,57–0,99) sem modelo.
  - Outras classes de roubo de celular: misto 1,62 (0,87–2,51), comércio médio 1,14 (0,84–1,49), trilho 1,12 (0,84–1,42).

**Implicação:**
- O "large pre-dawn peak" do modelo no popular não sustenta o tamanho: o número defensável é o sem modelo, 16% (9–23%).
- O 0,4 tem intervalo largo, e o sem modelo mostra uma queda de fim de semana menor e incerta.

**Frases propostas:**
- Results: "On low-standard housing the model places 41% of weekday robbery between 04:00 and 06:00 (95% interval 31–52%), but it overpredicts this share where it can be checked: in the 313 tracts where low-standard housing dominates expected robbery, 16% of weekday robberies with an exact hour occurred between 04:00 and 06:00 (9–23%, resampling districts) against 30% predicted, while in tracts dominated by commerce predicted and observed shares were both 6%."
- Results: "Robbery on low-standard housing is estimated at 0.4 times as frequent per day at weekends as on weekdays (95% interval 0.2–0.8), although tracts dominated by this class show a smaller and uncertain drop (0.83, 0.64–1.11)."
- Discussão: a frase "the routes from low-standard housing to transit before dawn" deve ser amaciada para "an exploratory pre-dawn excess near low-standard housing".

---

## 4. Concentração da queda do roubo de celular, 2022 → 2025 (R11)

**Pergunta:** a queda se espalhou pelo tecido residencial ou se concentrou em poucos lugares ou nos polos?

**Método:**
- Queda absoluta por setor, d = y₂₀₂₂ − y₂₀₂₅ (`fenotipo_setor_ano`, `n_total` e `n_geo`), nos 21.331 setores de exploração, e por segmento (eventos geocodificados ligados a até 60 m, só segmentos de exploração pelo setor correto, 143.452 segmentos).
- Parte da queda líquida nos 1%, 5% e 10% de unidades com maior queda.
- Nulo: queda proporcional uniforme com ruído de Poisson, μ₂₀₂₂ = (y₂₀₂₂ + y₂₀₂₅)/(1 + r), 200 simulações.
- Gini das quedas positivas.
- Composição por grupo dominante, com ≥ 50% do roubo esperado em 2022: polos (comércio médio e popular, serviços, trilho, terminal), residencial (popular, médio, esquina, alto padrão, favela), ruas, misto.

**Resultados (`n_total`; `n_geo` dá praticamente o mesmo):**
- Total: 72.078 → 43.136, uma queda líquida de 28.942. Caíram 49% dos setores e subiram 27%.
- Concentração por setor:

| | Parte da queda líquida | Parte do roubo de 2022 nesses setores | Nulo proporcional (IC) |
|---|---|---|---|
| 1% (214 setores) | 29% | 19% | 22% (21–23%) |
| 5% | 60% | 37% | 50% (49–51%) |
| 10% | 81% | 50% | 70% (69–71%) |

- Gini das quedas: 0,79, contra 0,79 (0,786–0,793) no nulo; o Gini do roubo de 2022 é 0,73.
- Por grupo dominante:
  - polos: 26,4% do roubo de 2022 e 23,7% da queda (razão 0,64);
  - residencial: 2,9% e 3,0% (0,59);
  - ruas: 11,2% e 12,6% (0,55);
  - misto: 59,4% e 60,7% (0,59).
- Dos 214 setores com maior queda, 81 são dominados por polos (40% da queda desse topo), 118 são mistos e 1 é residencial.
- Nos 313 setores dominados pelo popular, os 10% do topo levam 92% da queda, dentro do nulo (96%, IC 76–129%).
- **Segmentos:** o 1% com maior queda leva 46% da queda líquida, contra 38% (37–39%) no nulo, e tinha 23% do roubo de 2022. O Gini das quedas é 0,89, contra 0,92 no nulo.
- Não refiz a análise por segmento só nos segmentos residenciais. A queda do popular se concentra como o próprio crime (resultado acima).

**Implicação:**
- Em termos absolutos, a queda acompanhou a distribuição anterior do roubo, com um pouco mais de concentração no topo do que a queda proporcional daria. Não houve espalhamento "pelo tecido residencial": os setores residenciais têm 3% do roubo e deram 3% da queda.
- Os polos contribuíram quase na proporção do seu peso.
- O que se sustenta é relativo: as **taxas** caíram mais depressa no popular (0,56; com E corrigida 0,57) e na esquina (0,49; corrigida 0,29).
- A comparação com Seattle e Boston não se sustenta e deve sair (como o plano previa).

**Frase proposta (substitui a frase de Seattle e Boston):** "In absolute terms the fall tracked where robbery had been: tracts dominated by hubs, with 26% of 2022 robbery, contributed 24% of the net fall, and the 1% of tracts with the largest falls contributed 29%, somewhat more than a uniform proportional decline with Poisson noise would give (22%)."

---

## 5. Evento-estudo de aberturas e fechamentos (R6)

**Pergunta:** o que o desenho é e o que ele exclui.

**Desenho** (lido em `perturbacao.py` e confirmado nas saídas):
- **Tratamento:** mês do primeiro evento (abertura, ou fechamento pela data da situação final) do grupo no segmento entre 2023-01 e 2024-12, sem outro evento do mesmo grupo nos 12 meses anteriores. Na variante estrita, a checagem "limpa" usa só eventos estritos.
- **Eventos posteriores não são excluídos.** Nos 12 meses seguintes, 16–29% dos tratados têm outro evento do grupo (média de 0,21 a 0,41), e 2–3% têm mais de um no próprio mês 0. É o primeiro evento limpo, não um evento único.
- **Controle nunca tratado:** segmento sem nenhum evento do grupo, com qualquer filtro, em 2022-01..2025-12, na mesma célula distrito × classe de rua.
- **Segmentos que não entram:** os com eventos fora da janela de coorte ou não limpos não são tratados nem controles.
- **Estimador:** para o tratado i, da coorte g e da célula c, em cada e de −6 a 11:
  D_ie = (Y_i,g+e − Ȳ_i,[g−12, g−7]) − (C_c,g+e − C̄_c,[g−12, g−7]),
  onde C_c é a média mensal dos controles da célula. As médias são simples sobre os tratados, cada coorte pesa pelo seu tamanho. A pré-tendência é a média de e = −6..−1 e o efeito, de e = 0..11.
- É uma diferença em diferenças com nunca tratados por célula e base própria de cada coorte. Não é o Callaway–Sant'Anna: não há ponderação por escore de propensão nem regressão do desfecho, a base não é g − 1 e a incerteza não vem da função de influência.
- **Incerteza:** 200 reamostras dos distritos dos tratados, com as médias dos controles fixas, o que subestima um pouco a variância. Spillovers para segmentos vizinhos não são tratados.
- **Desfecho:** só eventos geocodificados de crime de rua (roubo e furto de celular e de outros bens), ligados a até 60 m e excluídos os que estão a até 100 m de uma estação.
- **Fechamentos:** as baixas pela data da situação final concentram-se no 2º semestre (2023: 5.978 no 2º semestre contra 2.447 no 1º), o que sugere baixas administrativas, não portas fechadas.

**Resultados recalculados** (setor correto, só exploração; efeito relativo à base, IC 95%):

| Variante | Tratados | Controles | Coortes 2023 / 2024 | Base / mês | Pré-tendência (rel.) | Efeito (rel.) | Meia-largura | Publicado (IC) |
|---|---|---|---|---|---|---|---|---|
| Abre bar, qualquer | 13.059 | 119.359 | 6.659 / 6.400 | 0,212 | −2% a +6% | +0,1% (−4,5 a +4,6) | 4,5% | −7,5 a +1,1 |
| Abre varejo, qualquer | 23.073 | 102.091 | 12.152 / 10.921 | 0,180 | −1% a +4% | +1,4% (−2,3 a +4,8) | 3,6% | −3,6 a +2,7 |
| Fecha bar, qualquer | 15.590 | 118.375 | 8.425 / 7.165 | 0,204 | −2% a +5% | −1,0% (−4,9 a +2,7) | 3,8% | −7,4 a +1,2 |
| Abre bar, estrito | 2.978 | 119.359 | 1.562 / 1.416 | 0,478 | −5% a +10% | +3,5% (−3,5 a +10,4) | 7,0% | −9,5 a +5,0 |
| Abre varejo, estrito | 5.716 | 102.091 | 3.034 / 2.682 | 0,364 | −3% a +7% | +1,5% (−4,1 a +8,8) | 6,4% | −3,4 a +4,7 |
| Fecha bar, estrito | 3.574 | 118.375 | 1.790 / 1.784 | 0,448 | −2% a +7% | +0,5% (−5,1 a +7,3) | 6,2% | −13,5 a +2,0 |

Todos os tratados têm célula com controle (cerca de 200–225 células).

**Publicado** (`evento_estudo.json`, com células e filtro de exploração errados, seção 0): 15.493; 26.742; 18.453; 3.469; 6.701 e 4.158 tratados; bases de 0,21 a 0,58. A união dos IC é −13,5% a +5,0%, de onde vem o "−14% a +5%". Uma redução de 10% não estava excluída em "fecha bar, estrito" (IC −13,5% a +2,0%).

**O que o desenho detecta:**
- recalculado, a união dos IC é **−5% a +10%**: reduções de 10% e de 14% ficam excluídas nas seis variantes;
- a meia-largura é de 3,6–4,5% nas variantes amplas e de 6,2–7,0% nas estritas;
- com poder de 80%, isso corresponde a efeitos de cerca de 1,4 × a meia-largura: ≈ 5–6% nas amplas e ≈ 9–10% nas estritas;
- os IC de 90% ficam dentro de ±10% em todas as variantes, mas essa margem não foi pré-especificada.

**Implicação:**
- "Effects outside −14% to +5%… excluded" precisa ser refeito com o setor correto.
- O texto deve relatar ausência de efeito detectado, com a margem explícita, e não "not a lever".

**Methods proposto (≈115 palavras):**

> Openings and closures of bars and restaurants and openings of retail establishments were dated from the business registry and linked to the nearest street segment (≤ 40 m). A segment was treated at its first such event in 2023–2024 with none in the preceding 12 months; later events were kept. For each treated segment and event month e, the change in geocoded street crime from its mean in months −12 to −7 was compared with the same change in the mean of never-treated segments (no such event in 2022–2025) of the same district and street class, and averaged over treated segments (pre-trend, e = −6 to −1; effect, e = 0 to 11). Intervals come from 200 bootstrap resamples of districts of treated segments, with control means fixed.

**Results proposto:** "Openings and closures of bars, restaurants and shops on street segments were followed by no detectable change in street crime over 12 months (95% intervals within −5% to +10% of the baseline rate in all six variants; Extended Data Fig. 3)."

**Discussão (substitui "not a lever"):** "Business openings and closures on a street segment were not followed by detectable changes in street crime within a year, although changes of about 5% (10% for the strictest definitions) cannot be excluded."

**Referência:** a citação de Callaway–Sant'Anna pode sair, ou virar "a difference-in-differences with never-treated controls (cf. ref.)".

---

## 6. Tabela S1 do benchmark (R13/R14)

**Arquivo:** `paper/review/parecer/tabela_S1_benchmark.md`. Contém:
- tabela em inglês com 20 métodos mais o bloco distrito × trimestre da violência letal;
- parágrafo de disponibilidade temporal (≈170 palavras);
- lista de verificações.

O CRPS está descrito, a pedido do coordenador, como "CRPS against the real-valued reconciled count (linear interpolation between the CRPS of the adjacent integers)". O código atual devolve o CRPS de ⌈y⌉ (Agente A), e nada foi repontuado.

**Achados que mudam o texto:**
1. **Tipagem de 2025: não entrou.** A tabela de modelagem e as previsões (2026-10-15) são anteriores a `lote_tipos_2025` (2026-10-16) e não têm coluna de tipo.
2. **O CNPJ do benchmark é o snapshot de 2026-09** (`covariates/cnpj.py`, `MES`), não o de 2025-12, que só alimenta o atlas. O estoque é reconstruído por data de início e de situação final, só com o endereço atual. A seção Data do manuscrito precisa dizer isso.
3. **Fotografias estáticas:** infraestrutura e OSM são de 2026; Censo 2022 e IPVS 2022 são estáticos. O IPTU do ano é emitido em janeiro e entra no mesmo ano, sem problema.
4. **φ:** é ajustado na janela de ajuste com médias dentro da amostra, não "on the 2025 tuning period" como diz o prereg §5.3. O ensemble é a exceção.
5. **Violência letal:** o LightGBM usa escores teóricos por distrito com covariáveis médias de **2025**, o ano de avaliação. É um vazamento pequeno; a correção é usar a média da janela de ajuste.
6. **Hiperparâmetros com proveniência incompleta:** 350 rodadas do LightGBM (o tuning deu 266 e 197) e 300 m do STKDE (o tuning deu 100 m) estão fixos em `zoo.py`.
7. **Duas rodadas de desenvolvimento:** o manuscrito cita a sem VIIRS (GNN, −0,025, `selection_dev.json`), mas `prereg/selection.json` foi atualizado pela rodada com VIIRS (LightGBM sem histórico).
8. **Persistência, sazonal ingênuo e hotspot prospectivo** vêm de uma rodada à parte, com calibração só em 2024. "Fitted on 2023–2024" não vale para eles.

---

## 7. Arquivos e testes

- `src/cityomics/atlas/ritmo_queda.py`: `run(log=print, partes=...)` grava o JSON. Funções principais: `pedestres`, `relogio_blocos`, `relogio_ic`, `queda_setores`, `segmentos_estrito`, `evento_estudo`, `ruas_setor_correto`, `sensibilidade_ruas`.
- `tests/test_parecer_ritmo.py`: 7 testes sintéticos, todos passando (`pytest -q tests/test_parecer_ritmo.py`). Cobrem: o nulo em blocos preserva os eventos por distrito × período e por setor; a concentração é 1 quando toda a queda está num setor; queda proporcional = crime inicial; Gini; o bootstrap da OD fica na zona; o `att` vetorizado é igual ao original.
- `data/processed/atlas/fenotipo/ritmo_queda.json`: só agregados, 94 KB.
- Execução completa: 46 min com OMP_NUM_THREADS = 4, pico de 1,6 GB.

---

## Quadro: afirmação → veredito

| Afirmação do manuscrito | Veredito | Base |
|---|---|---|
| "pedestrians" | **sustentada, com correção do Methods** | A bicicleta é 2% das pessoas-hora na rua; só a pé dá os mesmos números. O Methods deve excluir a bicicleta. |
| "risk per pedestrian peaks at 03:00, at 19 times its daily mean" | **qualificada** | Pico entre 1h e 3h (3h em 69% das réplicas); 19× com IC 13–30 (OD) ou 12–39 (OD + distritos); às 3h, 85 domicílios. |
| "the rhythm does not follow the crowd (median r = 0.03)" | **sustentada** | 0,018–0,042 (OD), −0,01 a 0,12 (conjunto), 0,028–0,034 por σ, 0,027 com E corrigida. |
| "0.4 times as frequent at weekends" | **qualificada** | IC 0,19–0,76; sem modelo nos setores dominados, 0,83 (0,64–1,11). |
| "phone theft clock P ≤ 0.005 both years" | **sustentada** | Blocos de dia e de mês: P ≤ 0,001 nos dois anos. O roubo de 2025 continua não significativo (0,15 e 0,46). |
| "fall spread across the residential fabric" (e o contraste com Seattle/Boston) | **não sustentada** | Os setores residenciais deram 3% da queda; os polos, 24% (com 26% do roubo). O topo de 1% levou 29%, contra 22% no nulo. Só a afirmação relativa sobre taxas se sustenta. |
| "effects outside −14% to +5% are excluded" | **não sustentada como publicada** | A análise publicada usou células e filtro de exploração errados e incluiu segmentos do cofre. Recalculado: −5% a +10%. |
| "single business openings or closures are not a lever within a year" | **não sustentada** | É ausência de efeito detectado, com efeitos de ~5–10% não excluídos, e 16–29% dos tratados têm eventos repetidos. |
| Extra: ρ = 0,75 (km × pedestre) | **qualificada** | IC 0,73–0,78 (OD), 0,58–0,85 (conjunto), 0,67–0,79 por σ; **0,58 com a exposição de ruas corrigida**. |
| Extra: "large pre-dawn peak" do modelo no popular | **qualificada** | Modelo 41% (31–52%), mas superestima os setores checáveis (30% previsto, 16% observado). |
