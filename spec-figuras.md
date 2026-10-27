# Spec — Figuras e narrativa "a cidade como tecido"

> Parte de [spec-overview.md](spec-overview.md). Depende de [spec-atlas.md](spec-atlas.md) (tipagem, nichos, comunicação, atribuição) e de [spec-benchmark.md](spec-benchmark.md) (previsões e testes). O explorador interativo está em [spec-explorer.md](spec-explorer.md).

**Em resumo:** um artigo único (D34) para a Nature Cities (D36), com seis figuras no padrão Nature.

> **Emenda de 2026-10-19 (D63):** a tese passa a ser a da **narrativa B** ([docs/NARRATIVA.md](docs/NARRATIVA.md)), substituindo a D35: *o crime é um fenótipo do tecido urbano* — a composição do lugar fixa onde, que crime e a que hora acontece; o mês a mês é ruído de Poisson em 96% dos setores, e a dinâmica mensal que existe mora em poucos polos. A tese antiga ("onde é tecido, quando é difícil") vira um caso particular. O roteiro abaixo (§3) já é o da narrativa B.

Os pilares, todos no desenvolvimento (2022–2025, fora do cofre):
- **onde:** a atribuição por classe de célula (comércio médio 70 roubos por km de frente por ano; validação pontual ρ = 0,93);
- **que crime:** 15 fenótipos com assinaturas distintas por classe (validação pontual mediana ρ = 0,85);
- **a que hora:** o relógio do tecido (39% do roubo de celular no residencial popular entre 4 h e 6 h), que não é o relógio da multidão (OD 2017);
- **estabilidade e memória:** 98% de permanência do tecido; memória do lugar além do tecido de 48% da variância;
- **limites:** o mês a mês é ruído de Poisson em 96% dos setores; métodos emprestados ganham 4%, já no teto.

As figuras priorizam beleza e clareza. As ressalvas vão para o texto, e nenhuma figura distorce (D47). Tudo que depende de dados é gerado por código e regerado depois do FREEZE (D50).

## 1. Metas e não-metas

**Metas**
- Seis figuras principais e até 10 Extended Data, prontas para submissão, regeráveis com `cityomics figures --periodo dev|2026`.
- Uma história coerente com a analogia biológica, nos termos da D37: a Fig. 1 explicita as equivalências; nas demais, os eixos usam termos urbanos e os métodos mantêm o nome da ômica.
- Resultados honestos: os resultados negativos (H1b, H2) entram como achado.

**Não-metas**
- Imagens geradas por IA (a política da Nature proíbe).
- Pontos de crime em qualquer figura.
- Qualquer uso de dados de 2026 antes do FREEZE.
- Títulos de painel que afirmam conclusões: a escolha foi o estilo Nature clássico (D46).

## 2. Equivalências (Fig. 1a)

| Transcriptômica espacial | Cidade (CityOmics) |
|---|---|
| Célula segmentada | Lote fiscal; favela = setor FCU do IBGE como pseudo-célula (D54) |
| Espaço intersticial e vasos | Ruas (segmentos do OSM) e estações/terminais como nós (D51) |
| Spot (Visium) | Setor censitário 2022 |
| Metacélula | Quadra fiscal (D59) |
| Região anatômica | Distrito |
| Gene | Atributo nativo do lote: IPTU, CNPJ por lote, MEI, testada, esquinas |
| Marcador | Covariável enriquecida num tipo ou domínio |
| Nicho e domínio | Composição de tipos no entorno |
| Ligante–receptor | Gerador/atrator no emissor → vulnerabilidade no receptor (teoria criminológica) |
| Fenótipo | Crime (desfecho; nunca define o tipo, D6/D53) |

## 3. Roteiro das figuras (183 mm de largura, 5–7 painéis cada; narrativa B, D63–D70)

O dado de cada painel vem de `data/processed/atlas/` (com `fenotipo/`, `presenca/` e `perturbacao/`) ou de `data/processed/modelo/`. Os layouts estão em `figures/figN.py`; os painéis reaproveitados das versões anteriores ficam em `figures/painel_*.py` e os rótulos em `figures/rotulos.py`.

### Fig. 1 — A cidade como tecido (sem mudança)
- **a.** Esquema tecido ↔ cidade (`figures/assets/fig1a_esquema.svg`, D50).
- **b.** "Corte histológico": 1,7 milhão de lotes por tipo, rasterizados a ~12 m sobre fundo escuro.
- **c–d.** ROIs em resolução de lote (centro e periferia), com contornos de setor e favelas FCU.

### Fig. 2 — Tipos e arquitetura
- **a.** UMAP da subamostra de lotes. **b.** Dotplot marcador × tipo. **c.** Composição dos spots (pizzas).
- **d.** Enriquecimento de vizinhança tipo × tipo (nulo restrito, D59). **e.** Mapa de domínios, com legenda dos nomes.
- **f.** Estabilidade da tipagem (ARI por resolução) e k-means.

### Fig. 3 — Fenótipo: que crime cada classe expressa (D64)
- **a.** Taxa atribuída de celular por classe (mesmas linhas de b).
- **b.** Matriz-assinatura classe × 15 fenótipos (tamanho = participação; cor = log2 do enriquecimento).
- **c.** Validação pontual por fenótipo (Spearman; fenótipos com < 80% de coordenadas não testados).
- **d.** Programas de crime (NMF, menor k ≥ 3 estável). **e.** Uso dos programas por setor (rasterizado; cofre em cinza).
- **f.** Sankey grupo teórico → classe → roubo de celular (D47, D57, D69).

### Fig. 4 — Ritmo: o relógio do tecido (D65)
- **a.** Perfil horário do roubo de celular por classe (hora exata).
- **b.** Crime × pessoas a pé na rua (OD 2017, dias úteis) em quatro classes.
- **c.** Risco por pedestre hora a hora na cidade.
- **d.** Réplica 2024 × 2025 dos desvios por período e distribuição nula da permutação dentro do distrito.
- **e.** Razão fim de semana / dia útil por classe.
- **f.** Taxa por km × risco por pedestre.

### Fig. 5 — Estabilidade, memória e mudança (D66)
- **a.** R² fora da amostra (tipos, genes, tecido, + covariáveis, média histórica).
- **b.** Decomposição da variância entre setores: tecido, memória estável, transitória.
- **c.** Persistência do resíduo além do tecido (defasagens de 1–3 anos).
- **d.** Transições anuais entre famílias (IPTU 2012–2025).
- **e.** Queda 2022→2025 por classe (razão relativa à cidade, IC por distrito).
- **f.** Variação 2022→2025 por fenótipo.

### Fig. 6 — Limites e confirmação (D67, D68)
- **a.** Curvas de captura com acaso, média histórica, ensemble, teto de ruído e oráculo (D58).
- **b.** Previsibilidade por escala: R² alcançado × R² máximo sem modelo (variância acima do Poisson).
- **c.** Concentração do excesso de variância mensal nos setores de maior contagem.
- **d.** Forest do ΔCRPS contra o NB-GLM. **e.** Celular × letal no órgão (D61). **f.** Equidade por quintil de renda.
- **g.** Quadro de confirmação: afirmações do atlas (pseudo-cofre no desenvolvimento; cofre depois da A11), H1a/H1b/H2 (2026 lacrado) e janela prospectiva.

### Extended Data (10; D70)
1. Tabela completa do benchmark. 2. Auditoria de equivalências (módulo ômico × análogo urbano × resultado × quem vence).
3. Comunicação exploratória (círculo, pares L–R, campo) e covariáveis por domínio. 4. Tabela multiverso da comunicação.
5. Knox, MISTy e Lee's L. 6. Co-ocorrência, colocation quotient e composição dos distritos.
7. Teoria: SHAP por grupo e cascata com sinal (D57). 8. Fora da amostra em detalhe (finalistas, mês a mês, acerto/erro, domínio, calibração, onde × quando).
9. Perturbação natural: evento-estudo de aberturas e fechamentos (nulo). 10. Painel de fenótipos: contagens e cobertura, escolha do k, fator multidão, renovação × variabilidade.

## 4. Sistema visual

- **Tamanho:**
  - larguras de 89, 120 e 183 mm, com altura máxima de 247 mm;
  - texto de 5 a 7 pt; letras de painel a, b, c em 8 pt, negrito e minúsculas;
  - linhas de 0,5 pt;
  - `pdf.fonttype = 42`;
  - PNG de 450 dpi para revisão.
- **Fonte:** Arial, se disponível; senão Liberation Sans, que tem as mesmas medidas (D62).
- **Fundo (D45):** mapas e ROIs em fundo escuro (`#0B0B0E`); gráficos estatísticos em fundo branco.
- **Paleta semântica dos tipos.** Cada família tem uma cor-base clara e uma variante escura (para os mapas). As cores finais saem de `viz/palette.py`, conforme os tipos que o Leiden encontrar:

  | Família | Clara | Escura (mapas) |
  |---|---|---|
  | Residencial horizontal | `#BFD7EA` | `#5B8FD0` |
  | Residencial vertical médio | `#6FA8DC` | `#7FB8F0` |
  | Residencial vertical alto | `#1F5A99` | `#A9CFFF` |
  | Comércio de rua | `#E8743B` | `#FF8A4C` |
  | Serviços e escritórios | `#8E6CC2` | `#B99BF0` |
  | Indústria e galpões | `#8C7B6B` | `#A89A8C` |
  | Favela (FCU) | `#E3B23C` | `#F2C14E` |
  | Vazio, verde, institucional | `#9CCB86` | `#6BCB77` |
  | Ruas | — | cinza-azulado `#3A4A5C` |
  | Estações | — | branco `#F5F5F5` |

- **Escalas contínuas:** `cmcrameri` (batlow, lajolla, vik), com fallback para magma, viridis e RdBu_r. As escalas divergentes têm o neutro no centro.
- **Grupos teóricos:**

  | Grupo | Cor |
  |---|---|
  | Atividade rotineira | `#E8743B` |
  | Desorganização social | `#8E6CC2` |
  | CPTED | `#2A9D8F` |
  | Mercado imobiliário | `#C9A227` |
  | Histórico de crime | `#5F6B7A` |
  | Identidade do tipo | `#B0B0B0` |

- **Densidade (D46):** 5 a 7 painéis só com letras. A primeira frase da legenda, em negrito, carrega a conclusão.
- **Princípio (D47):** beleza e clareza. Sem eixo truncado enganoso, sem escala falsa, sem fluxo que não se conserva.

## 5. Certeza (D44, D58)

A manchete é a captura em x% da área diante de cinco referências:
- o acaso;
- a média histórica;
- o modelo;
- o teto de ruído (captura esperada se o modelo fosse a verdade, simulada da preditiva NB);
- o oráculo (o ranking realizado).

Reportar em `n_total` e em `n_geo`. Painéis de apoio: calibração, mapa valor-por-alfa (risco × incerteza), acerto/erro no top 5% e habilidade por nicho.

## 6. Sankey (D47, D57)

- **Base:** crime esperado de 2025 = Σ_k exposição_k · λ_k(x) · exp(u). As classes de célula k são os tipos de lote (exposição = testada), as classes de rua (comprimento) e as estações (contagem) (D51).
- **Decomposição:** λ_k(x) = exp(β_k0 + Σ_g β_kg z_g), com os 4 grupos não temporais (o contexto temporal não entra no total anual). Shapley exato sobre as 16 coalizões, com a referência no setor médio (z = 0), documentada.
- **Nós:**
  - "identidade da classe" = v(∅);
  - grupos, em dois ramos: aumento e redução;
  - "espacial" = efeito u;
  - "não explicado".
- **Formato:** um painel por desfecho, em % do total. A cascata com sinal e intervalos vai para o Extended Data.

## 7. Ética nas figuras (D49, D60)

- Nenhum ponto de crime. Nenhum bairro ou favela nomeado. Termo do IBGE: "favelas e comunidades urbanas" (EN: favelas).
- Mapas de risco ou de acerto por setor são **rasterizados** dentro do PDF. Os Source Data saem no nível de distrito. O risco por setor só existe local e sob pedido.
- O objeto público é montado por lista branca: sem MEI por lote, sem `nm_fcu`, sem camadas de crime por lote.

## 8. Montagem e reprodutibilidade (D50, D52)

- **Código:**
  - `src/cityomics/viz/`: `style`, `palette`, `maps`, `sankey`, `chord`, `fields`;
  - `figures/fig1.py`…`fig6.py` e `figures/ed.py`;
  - `cityomics figures --periodo dev|2026 [--only figN]`.
- **Saída:** `figures/out/<periodo>/figN.pdf|png`, fora do git.
- **Fig. 1a:** SVG fixo, convertido por `cairosvg` e sobreposto em vetor com `pypdf`.
- **Período 2026:** só roda com o cofre aberto, e só lê o pacote de resultados com hash do FREEZE (D52).
- **Legendas:** `figures/legendas_<periodo>.md`, preenchidas a partir dos JSONs.

## 9. Testes e verificação

- `pytest`: os testes existentes e os novos de `tests/test_atlas.py` e `tests/test_viz.py`.
  - Atlas: o EM recupera λ, eficiência do Shapley, Knox ≈ 1 sob o nulo, as composições somam ao total, guarda contra `_2026`.
  - Figuras: largura em mm, fontes Type 42, menor texto ≥5 pt.
- `cityomics privacy-scan` estendido a zarr, h5ad, json, svg e csv (D60).
- Simulação de daltonismo e contraste (skill `scientific-visualization`) e revisão visual dos PNG.
- Os números das legendas batem com os JSONs.

## 10. Casos de borda

- Lotes sem IPTU (~2,3% em 2025) ficam como "sem cadastro" e não entram na tipagem; aparecem em cinza no mapa.
- CNPJ sem ligação ao lote fica contado no setor (D56).
- Setores sem lotes (parques, represas) ficam como "vazio".
- Favelas com lotes fiscais dentro: os lotes são marcados `em_favela`, e a área não é duplicada (D54).
- Cofre fechado: `--periodo 2026` falha com mensagem clara.

## 11. Segurança e privacidade

- Microdados (NUM_BO, endereço, coordenadas) e camadas de crime por lote só existem localmente.
- A validação pontual e o Knox rodam localmente, e só agregados saem.
- MEI por lote nunca sai da máquina (é dado de pessoa física no endereço de casa).
- `.gitignore` cobre `*.zarr`, `*.h5ad`, `figures/out/` e `explorer/`.
- 2026 só pelo cofre: nenhum código do atlas lê arquivos `*_2026*`, incluindo IPTU, ITBI, SP156 e CNPJ de 2026 (D55).

## Decisions Log

| ID | Topic | Decision | Rationale | Source | Date |
|---|---|---|---|---|---|
| D34 | Estrutura de publicação | Artigo único integrado (atlas + predição), substituindo D8; benchmark detalhado no suplemento; submissão após F7 (~meados de 2027) | O tecido explica onde (74% da variância entre setores) e o benchmark mede o que resta prever | Interview | 2026-10-16 |
| D35 | Afirmação central | "Onde é tecido, quando é difícil"; resultados negativos entram como achado | Única frase sustentada pelos resultados (ganho de 4% em CRPS; H1b e H2 negativas) | Interview | 2026-10-16 |
| D36 | Revista e formato | Nature Cities; padrão Nature (89/183 mm, 5–7 pt, Arial, letras de 8 pt, Type 42); sem imagens de IA generativa | Padrão mais restritivo; política da Nature | Interview | 2026-10-16 |
| D37 | Vocabulário | Híbrido: equivalências na Fig. 1; eixos urbanos; métodos com nome da ômica; inglês + PT | Reduz o risco de "geodemografia com nomes novos" | Interview | 2026-10-16 |
| D38 | Tipagem das células | Leiden sobre lotes com IPTU 2025 + CNPJ por lote + MEI separado + favelas como pseudo-células | Atividade econômica é central para o crime; favelas são 15% da população | Interview | 2026-10-16 |
| D39 | Comunicação | Multiverso exploratório: L–R criminológico (COMMOT + NicheNet), vizinhança, Hawkes/Knox entre tipos, OD 2017, MISTy, NCEM/SLX, GNN, Lee's L | O usuário quer avaliar várias abordagens e escolher pela narrativa | Interview | 2026-10-16 |
| D40 | Seleção das análises | Explorar até 2025 → escolher → emenda A11 antes do FREEZE → confirmar; tabela multiverso; não confirmado = exploratório (refinado por D53) | O cofre é a defesa contra o jardim dos caminhos que se bifurcam | Interview | 2026-10-16 |
| D41 | Violência letal | No corpo, como contraste; benchmark reduzido + atribuição agregada no distrito (refinado por D61) | Desfecho pré-registrado; contraste de "patologias" | Interview | 2026-10-16 |
| D42 | Destino celular | Versão reduzida: estabilidade do tecido; Laya no destino no suplemento (refinado por D56) | Sustenta D35 a custo moderado | Interview | 2026-10-16 |
| D43 | Roteiro e Fig. 1 | 6 figuras + Extended Data; Fig. 1 = mapa de 1,7 milhão de lotes + ROIs + faixa de esquema | Maior impacto na figura que decide a leitura | Interview | 2026-10-16 |
| D44 | Manchete de certeza | Captura em x% da área diante de referências; apoio: calibração, valor-por-alfa, acerto/erro, habilidade por nicho (refinado por D58) | Precisão no topo é inflada pela taxa-base | Interview | 2026-10-16 |
| D45 | Identidade visual | Mapas em fundo escuro, gráficos em fundo branco, paleta semântica; escalas uniformes; checagem de daltonismo | Cara de microscopia com legibilidade em 5–7 pt | Interview | 2026-10-16 |
| D46 | Densidade | Nature clássico: 5–7 painéis só com letras; texto na legenda | Escolha do usuário | Interview | 2026-10-16 |
| D47 | Grafo tripartite | Sankey com base de massa conservada; beleza e clareza nas figuras, ressalvas no texto, sem distorção (refinado por D57) | O usuário quer atrair o leitor | Interview | 2026-10-16 |
| D48 | Interativo | Explorador Vitessce sobre o AnnData do atlas, local agora e aberto na publicação | Visualizador nativo de transcriptômica espacial | Interview | 2026-10-16 |
| D49 | Ética do explorador | Público: risco só por distrito ou BYM2; setor só local; figuras estáticas podem mostrar o setor; termo do IBGE; sem nomes; sem pontos (refinado por D60) | D11 e risco de estigma | Interview | 2026-10-16 |
| D50 | Montagem | Painéis em código, regeráveis por período; só o esquema da Fig. 1a é SVG desenhado à mão | Refazer depois do FREEZE sem retrabalho manual | Interview | 2026-10-16 |
| D51 | Crime fora das células | Ruas (segmentos do grafo OSM, por classe) e estações/terminais entram como classes de célula com λ próprio ("espaço intersticial e vasos"); a exposição dos lotes é a testada do IPTU; a validação pontual liga o ponto ao segmento de rua e aos lotes lindeiros. Resolvido sob delegação | 79% do roubo de celular é em via pública e 9,5% em estações; lote como única célula daria λ sem sentido | Red Team | 2026-10-16 |
| D52 | FREEZE em duas etapas | FREEZE-A até o início de dez/2026 (benchmark + features mínimas do atlas para H3, com hash dos rótulos por lote) e FREEZE-B (A11 descritiva + lista do multiverso) antes de abrir 2026; `freeze.py` passa a incluir os artefatos do atlas; figuras de 2026 leem só o pacote com hash. O ato de congelar continua sendo do autor. Resolvido sob delegação | A janela prospectiva começa em nov/2026, antes do FREEZE único previsto (~mar/2027), e o atlas não estava no manifesto | Red Team | 2026-10-16 |
| D53 | Escolha sem crime e cofre espacial | Tipagem (genes, resolução, k) fixada só por critérios sem crime (ARI, marcadores); ~20% dos distritos sorteados com semente registrada formam um cofre espacial excluído de toda análise de crime do atlas até a confirmação; pseudo-confirmação 2024→2025 para calibrar; família própria do atlas com Holm; 2026 vira teste de estabilidade. Resolvido sob delegação | D40 deixava o crime escolher a tipagem; a confirmação temporal discrimina pouco (Spearman 2024→2025 = 0,82) | Red Team | 2026-10-16 |
| D54 | Favelas | Pseudo-células = setores FCU do IBGE (um por setor, exposição em lotes-equivalentes calculada pelos domicílios); os polígonos HABISP saem da tipagem; lotes fiscais dentro de favelas ficam marcados `em_favela`, sem duplicar área. Resolvido sob delegação | HABISP é outra definição, erra a composição de ~3/4 dos setores FCU e infla λ pelo tamanho | Red Team | 2026-10-16 |
| D55 | H3, H4 e 2026 | H3 compara o modelo com atlas contra o mesmo modelo com genes do lote agregados por setor sem tipagem (comparador na Fig. 4c); H4 redefinida com os genes de D38 e Holm recalculado (emenda A11); leitura de IPTU, ITBI, SP156 e CNPJ de 2026 bloqueada por código no atlas e nas figuras. Resolvido sob delegação | O ganho de H3 poderia vir só do IPTU novo; H4 mudou sem emenda; arquivos de 2026 estão fora do cofre | Red Team | 2026-10-16 |
| D56 | CNPJ por lote e data | Ligação CNPJ↔IPTU pelo endereço (CEP + número → SQL → lote), com o CNEFE só como reserva; snapshot do CNPJ de 2025-12 para a tipagem de 2025; destino celular só com transições anuais do IPTU (2012→2025), com 2021 mascarado. Resolvido sob delegação | O CNEFE cai dentro do lote só em 31,7% dos casos; o snapshot de 2026-09 traria informação de 2026 | Red Team | 2026-10-16 |
| D57 | Sankey corrigido | Mantido por decisão do usuário (D47), mas com ramos separados de aumento e redução, nó espacial (u) e "não explicado", referência no setor médio e sem contexto temporal; a cascata com sinal e intervalos vai para o Extended Data. Resolvido sob delegação; a recomendação do red-team (trocar por cascata) contrariava uma escolha explícita do usuário | Shapley tem sinal, falta u e o contexto temporal é degenerado no total anual | Red Team | 2026-10-16 |
| D58 | Referências da captura | Acaso, média histórica, modelo, teto de ruído simulado e oráculo, em `n_total` e `n_geo`. Resolvido sob delegação | O modelo já está a ~95% do teto de ruído; o oráculo sozinho sugere uma folga que não existe | Red Team | 2026-10-16 |
| D59 | Escala dos nichos e da comunicação | Metacélulas por quadra fiscal (47 mil) para L–R, co-ocorrência e campos; lotes completos só na tipagem e no enriquecimento de vizinhança; nulos com permutação restrita (dentro do distrito e do decil de densidade); estabilidade do Leiden em 10–20 subamostras. Resolvido sob delegação | COMMOT e co-ocorrência não cabem em 1,7 milhão de lotes; o nulo global vira "tudo significativo" | Red Team | 2026-10-16 |
| D60 | Coerência de privacidade | D49 mantida; mapas por setor rasterizados nas figuras; Source Data por distrito; objeto público por lista branca (sem MEI por lote, sem `nm_fcu`, sem crime por lote); scanner de privacidade estendido a zarr, h5ad, json, svg e csv; `.gitignore` com `*.zarr`, `*.h5ad`, `figures/out/`, `explorer/`. Resolvido sob delegação; a opção do red-team de publicar o risco por setor contrariava a escolha do usuário | Polígonos vetoriais e Source Data permitiriam extrair o valor de cada setor; o scanner não via os novos formatos | Red Team | 2026-10-16 |
| D61 | Contraste celular × letal | O celular também roda em distrito × trimestre como comparador pareado; contraste baseado no desenvolvimento de 2025; letal de 2026 rotulado como exposto; atribuição do letal com 4–5 macrotipos. Resolvido sob delegação | Escala diferente confundiria desfecho com agregação; 96 distritos não identificam 15 tipos | Red Team | 2026-10-16 |
| D62 | Dependências | Um ambiente só (`cityomics`), com os pacotes novos fixados em `environment.yml` e `requirements-pip.lock` (vitessce, cmcrameri, cairosvg, pypdf); atribuição em numpy/scipy (sem INLA); Knox próprio em tempo contínuo no lugar do Hawkes discreto; Simples e OD baixados agora; Arial se possível, senão Liberation Sans; o lock entra no FREEZE. Resolvido sob delegação | Evita quebrar o ambiente travado; o Hawkes discreto atual mede persistência, não excitação | Red Team | 2026-10-16 |
| D63 | Narrativa | **Substitui D35.** Narrativa B: "o crime é um fenótipo do tecido urbano" (onde, que crime, a que hora; o mês a mês é ruído fora dos polos); roteiro das seis figuras e dos dez ED refeito | Análise de 2026-10-19 (`docs/NARRATIVA.md`) e pilotos P1–P7 nos distritos de exploração; pedido do autor ("implemente tudo o que for necessário para a narrativa B") | Interview | 2026-10-19 |
| D64 | Painel de fenótipos | 15 fenótipos da base principal (sem iniciativa policial, sem estupro, lesão dolosa só fora de residências, BOs de celular fora de "outros"); assinaturas por EM do Poisson linear; programas por NMF com o menor k ≥ 3 estável; Fig. 3 | O tecido define que crime, não só quanto (11 classes distintas no topo; validação mediana ρ = 0,85) | Interview | 2026-10-19 |
| D65 | Relógio e população presente | Relógio por classe (período e hora exata; permutação dentro do distrito); OD 2017 do Metrô (baixada com autorização do autor em 2026-10-19; sha256 no manifesto) como exposição: presença e pessoas a pé na rua; Fig. 4 | O relógio é de vigilância natural, não de multidão (correlação mediana crime × pedestres = 0,03) | Interview | 2026-10-19 |
| D66 | Estabilidade, memória e mudança | Fig. 5 com a decomposição tecido × memória estável × transitória e a queda 2022→2025 por classe com o tecido fixo; evento-estudo de CNPJ no ED9 como nulo | Memória além do tecido = 48% da variância; a queda poupou os polos; aberturas e fechamentos não movem o crime em 12 meses | Interview | 2026-10-19 |
| D67 | Limite de previsibilidade | Fig. 6 com R² × R² máximo sem modelo por escala e o teste de dispersão de Poisson por setor | O mês a mês é Poisson em 96% dos setores; 88% do excesso está no 1% de setores com mais crime | Interview | 2026-10-19 |
| D68 | Família do atlas para B | A-R1, A-R2, A-R6, A-R7, A-R8 com Holm (A-R3/A-R4 exploratórias; A-R5 opcional, falha no desenvolvimento); código em `atlas/confirmacao.py`, bloqueado até a A11 datada; ensaio em pseudo-cofre | O cofre continua sendo a defesa contra o jardim dos caminhos que se bifurcam (D40, D53) | Interview | 2026-10-19 |
| D69 | Sankey | Mantido no corpo, agora como Fig. 3f (D47, D57) | Decisão anterior do usuário | Interview | 2026-10-19 |
| D70 | Extended Data | Dez ED na ordem do §3; comunicação, SHAP e detalhes fora da amostra saem do corpo | Corpo dedicado à tese B; o que não acrescenta vai para a auditoria (ED2) | Interview | 2026-10-19 |

## Dependency Graph & Implementation Order

```
units/lotes + IPTU 2025 (testada, esquinas, endereço) + CNPJ 2025-12 (+ Simples)
   └─► atlas/genes_lote ─► atlas/typing ─┬─► atlas/spots (setor, quadra, distrito; FCU)
                                         ├─► atlas/niches (vizinhança, domínios, metacélulas)
                                         ├─► atlas/fate (IPTU anual)
OSM drive + estações ─► atlas/streets ───┤
cofre espacial (D53) ───────────────────►├─► atlas/attribution (λ por classe; Sankey; validação pontual)
                                         ├─► atlas/communication (multiverso) ─► tabela multiverso ─► A11 (rascunho)
                                         ├─► atlas/variance (com comparador sem tipagem)
benchmark dev (pred_dev_*) ──────────────┼─► atlas/predictors (SHAP)  · models/letal_run (+ celular distrito×trimestre)
                                         ▼
viz/style + palette + maps + sankey + chord + fields ─► figures/fig1..6, ed ─► legendas
                                         └─► explorer (spec-explorer.md)
FREEZE-A (autor, até dez/2026) ─► FREEZE-B (autor) ─► abrir 2026 ─► figures --periodo 2026
```

1. `genes_lote`, `streets` e o sorteio do cofre espacial (bloqueiam o resto).
2. `typing`, depois `spots`.
3. `niches`, `attribution`, `variance`, `predictors` e `letal_run`, em paralelo.
4. `communication` (multiverso) e `fate`.
5. `viz` e as Figs. 1, 2, 4 e 5; depois as Figs. 3 e 6 e o Extended Data.
6. Explorador.
7. Documentação, rascunho da A11, extensão de `freeze.py` e `privacy.py`.

## Tarefas

- [x] Fase A: specs, emendas e estado da entrevista
- [x] `atlas/genes_lote.py` (IPTU 2025 + CNPJ 2025-12 por endereço + MEI)
- [x] `atlas/streets.py` (segmentos e estações como células)
- [x] cofre espacial de distritos em `atlas/guard.py` (semente registrada)
- [x] `atlas/typing.py` (Leiden, estabilidade, marcadores, k-means)
- [x] `atlas/spots.py` (composição por setor, quadra e distrito; FCU)
- [x] `atlas/niches.py` (vizinhança com nulo restrito; domínios; metacélulas)
- [x] `atlas/attribution.py` (λ por classe; Sankey; validação pontual)
- [x] `atlas/communication.py` (multiverso)
- [x] `atlas/fate.py` (transições anuais do IPTU)
- [x] `atlas/variance.py` e `atlas/predictors.py`
- [x] `models/letal_run.py` (+ celular distrito × trimestre)
- [x] `viz/*` e `figures/fig1..6`, `ed`, legendas
- [x] Explorador Vitessce
- [x] Documentação, A11 (rascunho), `freeze.py` e `privacy.py` estendidos, commits

### Narrativa B (2026-10-19)
- [x] Pilotos P1–P7 (`atlas/fenotipo.py`, `presenca.py`, `memoria.py`, `previsibilidade.py`, `perturbacao.py`)
- [x] OD 2017 baixada (autorização do autor) e processada em presença e pessoas na rua por setor × hora
- [x] Confirmação no cofre pré-especificada (`atlas/confirmacao.py`) e ensaio em pseudo-cofre
- [x] Figs. 2–6 refeitas, ED1–ED10, legendas geradas pelo `cityomics figures`
- [ ] Autor: datar a A11 com a família de B e rodar a confirmação no cofre (uma vez)
- [ ] Autor: FREEZE-A e FREEZE-B
