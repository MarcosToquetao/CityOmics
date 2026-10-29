# Gêmeos de tecido: contexto espacial do "estado além do tipo"

Análise exploratória posterior ao artigo (2026-10-28). **Não altera o manuscrito.** Roda só nos 77 distritos
de exploração (D53), sem 2026, com crime de celular 2022–2025 e fenótipos da SSP. Tudo é local; as tabelas
por setor não saem do computador (D49/D60).

**Pergunta.** Setores com a mesma composição de lotes divergem em quanto crime, que crime, a que hora e
tendência. Algum contexto espacial (vizinhança, bordas, rede viária, fluxos, delegacia) explica isso?

**Código.** `src/cityomics/atlas/contexto.py` (resíduos, gêmeos, Moran, controles),
`contexto_vizinhanca.py` (anéis, bordas, delegacia, interações, motivos, contágio) e `contexto_grafo.py`
(rede viária, OD 2023, GNN) e `contexto_extra.py` (passo 4: comparação equalizada, tendência mensal, incerteza do OD, interação, MGWR, GNN com sementes). Rodam com `cityomics atlas run contexto contexto_vizinhanca contexto_rede
contexto_od contexto_gnn contexto_figura contexto_tendencia contexto_equalizado contexto_od_incerteza contexto_od_interacao contexto_mgwr contexto_gnn_sementes contexto_figura_extra contexto_teto contexto_teto_resumo`; o passo 5 está em `contexto_teto.py`. Saídas em `data/processed/atlas/contexto/` (`contexto.json`,
`vizinhanca.json`, `grafo.json`); figuras em `figures/out/exploratorio/contexto/`.

## Desenho

- **Resíduo do tecido** por setor em quatro desfechos, todos encolhidos (gama-Poisson ou pseudocontagem):
  quanto (celular), que crime (afastamento da mistura de 15 fenótipos), a que hora (parte noturna) e
  tendência 2022–2025. Reproduz a decomposição do artigo: 42% tecido, 46% persistente, 23% transitória,
  −11% covariância.
- **Gêmeos de tecido:** 35 mil pares com Hellinger mediano 0,17 (0,62 ao acaso), mesmo tamanho e densidade.
- **Teste:** o contexto reduz o resíduo? R² fora da amostra com CV por distrito (LightGBM), efeito dentro
  do distrito com bootstrap por distrito, e correlação entre os resíduos dos gêmeos antes e depois.

## Resultados

| Pergunta | Achado |
|---|---|
| O que sobra depois do tecido próprio? | O tecido próprio não linear explica 26% do resíduo de "quanto". Retirado isso, gêmeos a mais de 3 km deixam de se parecer (r 0,28 → 0). |
| Em que escala há contexto? | Só até cerca de 1 km (r entre gêmeos 0,39; 0,11 a 1–3 km; ≈ 0 acima). Alcance do correlograma: 750 m a 2,5 km. |
| Os anéis de vizinhança ajudam? | Pouco: R² de "quanto" 0,27 → 0,35 (+0,06 do 1º anel; +0,01 do 2º). O resíduo entre gêmeos a menos de 1 km quase não cai (0,38 → 0,34). |
| Bordas e contraste? | Efeitos pequenos: entropia da vizinhança +0,07 DP; contraste −0,03 a −0,04; favela ao lado de setor formal reduz o crime noturno (−0,045). Menos de 1,1% da variância dentro do distrito. |
| Salto na divisa de delegacia? | Não para quanto (β = −0,02; IC −0,27 a 0,17). Sim, parcial, para roubo-outros (0,51; IC 0,11–0,93) e furto de veículo (0,37; IC 0,09–0,69). Celular: sem salto. |
| Tipos interagem? | 55% da contribuição do modelo é interação. Saturação vertical: a contribuição de "vertical residencial e misto" cai de +0,15 a −1,00 ao longo dos quintis. |
| Subcontextos sem supervisão? | Não separam o resíduo (η² = 0,007, quase igual ao acaso). |
| Contágio? | Modelos espaciais acusam dependência (SAR ρ = 0,44; SEM λ = 0,51; SDM é o melhor pelo AIC). No painel anual, o nível dos vizinhos prevê o setor (β = +0,17; IC 0,15–0,19) e o choque quase não passa (+0,04). É estado compartilhado, não contágio. |
| Rede viária? | Centralidade e permeabilidade sobem o R² de "quanto" 0,27 → 0,30; compor o entorno pela rede em vez do círculo não ajuda (0,342 contra 0,342 a 800 m). |
| Fluxos OD 2023? | R² de "quanto" 0,27 → 0,36 e o resíduo entre gêmeos a menos de 1 km cai de 0,38 para 0,32. **Ressalva do passo 4:** com o mesmo número de variáveis por bloco, o OD empata com a composição dos círculos de 1 a 2 km (ver abaixo); ele não é um contexto único. Efeitos: diversidade de origens (+0,18 DP; IC 0,11–0,27), visitantes (+0,16), visitantes por morador (+0,14), renda dos visitantes menos a dos moradores (+0,07). Sem efeito no horário nem em "que crime". |
| GNN? | Rainha, 0 saltos: R² 0,23; 1 salto: 0,31; 2: 0,32; 3: 0,31. Um salto já pega quase tudo. A rede viária de 800 m (0,33) não supera a rainha por mais de 0,01. Para "que crime" e horário os saltos não ajudam. |

**Horário.** É quase todo contexto e quase nada de composição. O próprio tecido explica 3%, o círculo de
2 km acrescenta 6% (setores sem cadastro, indústria e comércio, e a distância ao metrô). A tendência
2022–2025 é ruído (R² ≈ 0).

## Leitura

1. **O estado além do tipo tem três partes, e só uma é "lugar".**
   - Uma parte é tecido mal modelado (interações entre tipos, sobretudo a saturação vertical): dá 26% do
     resíduo e é o que faz gêmeos distantes se parecerem.
   - Uma parte é contexto local de até cerca de 1 km. Fluxos OD e a composição dos círculos de 1 a 2 km
     explicam o mesmo tanto dele (passo 4): os contextos se sobrepõem, e nenhum é exclusivo.
   - O restante, a maior parte, não é explicado por nenhum contexto testado.
2. **A vizinhança compartilha um estado, não transmite choques.** O nível do resíduo é correlacionado entre
   vizinhos e persistente, mas mudanças de um ano não se propagam.
3. **Delegacia não é só ruído de registro.** Para o celular não há salto na divisa. O efeito aparece em
   roubo-outros e furto de veículo, e é compatível com prática de registro nesses tipos.
4. **Resultado negativo útil:** bordas de composição, subcontextos sem supervisão e rede viária não
   adicionam informação além do 1º anel e do tecido próprio.

## Passo 4: o que ficou pendente

Comparação com o **mesmo número de variáveis** (cada contexto reduzido a 8 dimensões por PCA, sobre o tecido
próprio; um bloco de ruído de 8 dimensões dá ganho de −0,011):

| Bloco | Ganho de R² em "quanto" |
|---|---|
| Fluxos OD | +0,085 |
| Círculo de 1 km | +0,084 |
| Círculo de 2 km | +0,081 |
| Círculo de 500 m | +0,067 |
| 2º anel rainha | +0,062 |
| Composição pela rede viária (800 m) | +0,060 |
| Posição (estações, corredores, favelas, centro) | +0,058 |
| 1º anel rainha | +0,050 |
| Métricas da rede viária | +0,033 |
| **Todos juntos** | **+0,126** |

- **Correção do passo 2:** o OD não é o contexto que "mais ajuda". Com o mesmo número de variáveis ele empata
  com os círculos de 1 e 2 km. O que parecia vantagem do OD vinha de ele trazer oito indicadores desenhados
  para o crime contra blocos de composição mais pesados.
- **Redundância:** 1º anel + OD dá +0,095 (a soma isolada seria 0,135); 1º anel + 2 km + posição, +0,101; todos
  juntos, +0,126. Os contextos descrevem em boa parte a mesma geografia.
- **Horário:** só o círculo de 2 km ajuda (+0,042); o OD dá +0,002.
- **Quanto, sem distrito:** nenhum bloco sozinho passa de +0,011; todos juntos dão +0,027.
- **Que crime:** todos os blocos entre +0,012 e +0,024.

**OD, incerteza e 2017.** O ganho de R² em "quanto" nas 24 réplicas do bootstrap de domicílios fica entre +0,082
e +0,094. Efeitos em "quanto": diversidade de origens +0,18 (bootstrap 0,15–0,21), visitantes +0,16, visitantes
por morador +0,14. Com a OD 2017 (63 mil viagens) o resultado é praticamente o mesmo: R² de 0,360, diversidade
+0,22, e as duas edições juntas não somam (0,359). A correlação entre os setores das duas OD é 0,87 em visitantes,
0,95 em diversidade de origens e 0,22 em fração noturna. O fluxo captura geografia estável da cidade. Os
intervalos do bootstrap só medem a amostragem da OD, e em alguns casos não contêm a estimativa pontual
(viés do bootstrap).

**Interação tipo × fluxo.** O efeito da diversidade de origens varia de +0,07 a +0,35 entre os sete domínios
(maior nos verticais, nas arteriais e nas coletoras), mas a heterogeneidade não passa de p = 0,09 por domínio e
p = 0,06 por tipo dominante. Nas outras oito combinações (fluxo × desfecho) p vai de 0,06 a 0,89. Nada
sobrevive a correção por múltiplos testes.

**Tendência mensal (48 meses).**
- Existe sinal: confiabilidade entre meses pares e ímpares r = 0,43 (0,60 com Spearman-Brown), e correlação de
  0,69 com a tendência anual.
- Sinal espacial fraco: Moran I = 0,085 (nulo 0,02; p = 0,005). Os gêmeos a menos de 1 km não se parecem (r = 0,02).
- Nenhum contexto a prevê: R² do tecido próprio −0,03; todos os blocos de contexto ficam entre −0,024 e +0,004;
  bordas, delegacia (β = 0,03; IC −0,52 a 0,48) e OD também dão nulo.

**MGWR / GWR.** As taxas por classe **não** variam de forma útil no espaço. O GWR validado por distrito prevê
fora da amostra com R² de 0,06, contra 0,33 do OLS global, e todas as bandas ficaram no piso de 151 vizinhos
(o modelo "quer" janelas ainda menores, o que indica ruído). O primeiro MGWR (sem piso) divergiu numericamente
e foi descartado. Cautela: o teste é duro para o GWR (o distrito de teste fica cercado por treino), e o ajuste
é gaussiano sobre contagens com 2.500 setores e 5 classes.

**GNN com cinco sementes.** Estável (DP ≤ 0,008): R² de "quanto" 0,226 sem vizinhos, 0,305 com 1 salto, 0,317
com 2; a rede viária de 800 m dá 0,325. Tendência mensal ≈ 0 em todas as configurações.

## Passo 5: um modelo único com todos os contextos

Um LightGBM recebe o tecido próprio e **todos** os blocos de contexto em dimensão completa (224 variáveis:
anéis rainha, círculos de 250 m a 2 km, posição, rede viária, fluxos OD, bordas), com validação por distrito. Numa
segunda variante entra o bloco socioeconômico do setor e do 1º anel (censo 2022 e IPVS; **sem raça/cor**, por ser
variável ecológica e fácil de ler errado). A seleção de variáveis é aninhada: o ranking e o número de variáveis
(10 a 160) saem só do treino; o teste só avalia.

| Desfecho | Só tecido | Modelo único | + seleção | + socioeconômico | Teto (confiabilidade) |
|---|---|---|---|---|---|
| Quanto | 0,266 | **0,396** | 0,392 | 0,403 | 0,90 |
| Quanto, sem distrito | 0,119 | 0,151 | 0,128 | 0,165 | — |
| Que crime | 0,180 | 0,219 | 0,206 | 0,226 | — |
| A que hora | 0,009 | 0,066 | 0,051 | 0,066 | 0,50 |
| Tendência mensal | −0,026 | −0,051 | −0,059 | — | — |

- **Teto.** A parte reprodutível do resíduo (metades de meses pares e ímpares, Spearman-Brown) é 0,90 em "quanto"
  e 0,50 em "a que hora". O modelo único explica **44% do reprodutível de "quanto"** (o tecido sozinho, 30%) e
  **13% do de "a que hora"**. Sobra, em "quanto", cerca de 0,50 de variância reprodutível e sem explicação.
- **A seleção não ajuda.** Em todos os desfechos o modelo completo é igual ou melhor que o selecionado (as dobras
  escolhem 40 a 160 variáveis). O bloco socioeconômico acrescenta +0,007 em "quanto" e +0,014 em "quanto sem distrito".
- **Contribuição única pequena e redundância.** Retirar um bloco do modelo completo custa no máximo 0,014 de R²
  em "quanto" (rede viária e OD, 0,014; círculos, 0,011; os demais, ≤ 0,003). Cada contexto é em boa parte
  substituível pelos outros. Em |SHAP|: tecido 28%, círculos 28%, OD 12%, anéis rainha 11%, rede 11%.
- **Horário.** Quase tudo vem dos círculos de 1 a 2 km (perda de 0,024 ao retirá-los, 45% do |SHAP|). OD e anéis
  rainha contribuem zero.
- **Tendência mensal.** Nenhum contexto a prevê (R² negativo em todos os modelos).
- **O que sobra é o ponto central.** Depois do modelo único, gêmeos a menos de 1 km ainda se parecem (r = 0,33 em
  "quanto", contra 0,38 só com o tecido; 0,21 em "a que hora", contra 0,24). O Moran do resíduo cai só de 0,244 para
  0,175 (nulo 0,056). Acima de 1 km a semelhança desaparece (r ≤ 0,05). Todo o contexto composicional, de rede e de
  fluxo captura apenas cerca de um sétimo da semelhança de curtíssimo alcance, e o resto é estrutura local que
  nenhuma variável testada descreve.
- **Hipótese não testada.** Esse resíduo local (setores vizinhos parecidos entre si, mas diferentes do esperado) é
  compatível com fatores que o cadastro não vê: uso real de calçadas e pontos específicos (ambulantes, comércio
  informal), gestão e controle territorial, policiamento e iluminação. A iluminação (fração de faces de quadra
  com iluminação, do censo) aparece entre as variáveis estáveis da seleção em "que crime", mas o dado é de
  cobertura, não de qualidade.

**Limites do passo 5.** O teto mede reprodutibilidade, não explicabilidade: parte do resíduo reprodutível pode ser
só persistência do próprio crime. Os atributos não usam crime, então não há vazamento, mas a autocorrelação entre
distritos vizinhos favorece levemente a validação por distrito. O boosting com 15,9 mil setores pode subestimar o
que um modelo mais flexível ou dados mais ricos capturariam.

## Limites

- Todas as associações são correlações no resíduo de um modelo de uma taxa por classe; "contexto" aqui
  é composição, posição e fluxo, não mecanismo.
- A explicação por gradiente integrado acerta o sentido de 60% dos pares discordantes e atribui 68% às
  vizinhas; trate como indicação, não como resultado.
- A OD 2023 é amostra de domicílios (41 mil viagens a destino que não é a casa); os fluxos por setor são
  suavizados com σ = 500 m. O bootstrap cobre só a amostragem da OD, não a do crime nem a dos distritos.
- A reconciliação reparte os eventos sem coordenada em proporção; o controle com `n_geo` não testa nada.
- Um modelo de efeito fixo de distrito explica menos de 1,1% do resíduo nas bordas; o R² é baixo porque o
  resíduo é majoritariamente ruído de Poisson em setores com pouco crime.

## Próximos passos possíveis (não feitos)

- Testar o resíduo local de até 1 km contra dados novos: iluminação pública (qualidade), ambulantes e operações policiais por área.
- Um modelo de efeitos aleatórios espaciais (BYM2) para separar o que é estrutura local do que é ruído.
- Dados de iluminação pública e de operações policiais por área, que o artigo cita como não testados.
