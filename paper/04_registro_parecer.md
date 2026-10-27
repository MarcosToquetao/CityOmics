# Registro da revisão pelo parecer crítico (2026-10-20 a 2026-10-26)

**Arquivos:**
- parecer: `review/parecer/00_parecer_original.md`;
- plano de triagem: `03_plano_parecer.md`;
- relatórios dos agentes: `review/parecer/{A,C,D,E,F,G}_*.md`. Os números de A, C e G são intermediários; os válidos estão no manuscrito e nos JSON citados abaixo.

**Versões preservadas:**
- `versoes/v1_original/`: o manuscrito e o PDF anteriores ao parecer;
- `versoes/v2_tipos_publicados_ruas_corrigidas/`: o texto intermediário;
- `data/processed/_versoes/`: os dados de cada versão.

**Situação:** a versão atual está em `manuscript_src.md`, gerado como `manuscript.md`, `.docx` e `manuscript_figuras.pdf`. As Informações Suplementares estão em `supplementary_src.md`, gerado como `supplementary.md` e `.docx`.

## 1. Três problemas que o parecer não apontou, encontrados ao verificá-lo

| Problema | Efeito | Correção | Evidência |
|---|---|---|---|
| **CRPS com contagem fracionária.** `eval/scores.crps_nb` dava o CRPS de ⌈y⌉, e não o de y real. A fórmula estava escrita assim no próprio pré-registro (§5.3, A6). | O "−4%" do benchmark estava errado; o ranking dos modelos mudava. | Fórmula corrigida em `scores.py` (a antiga fica como `crps_nb_registrado`). Benchmark repontuado com as previsões gravadas: o ensemble ficou −6,4% (IC −0,023 a −0,011) contra o GLM, e o melhor modelo único passou a ser o LightGBM núcleo (−4,9%). `prereg/selection.json` **não foi alterado**: a mudança de seleção fica na emenda A12. | `prereg/A12_DRAFT.md`, `src/cityomics/models/repontua_crps.py`, `prereg/selection_dev.json` (o anterior está em `selection_dev_crps_registrado.json`) |
| **Setor dos segmentos de rua trocado** (`atlas/streets.py`). O índice desalinhava os pontos médios, e só 0,2% dos segmentos estavam no setor certo. | A exposição de ruas de todo o atlas estava errada. O evento-estudo usou segmentos de distritos do cofre (20%). | Corrigido, com teste (`tests/test_streets.py`). Atlas refeito. Exposição do cofre declarada em Methods e na Tabela S2. | `review/parecer/C_ritmo_queda.md` §0 |
| **Tipagem não reproduzível.** Os 12 tipos tinham sido calculados numa tabela de lotes anterior à unificação dos polígonos; refeitos na tabela atual, a concordância era de ARI = 0,58. | O "comércio de rua médio" e as taxas de destaque dependiam dessa versão. | **Decisão do autor: refazer.** kNN exato no Leiden (rótulos determinísticos), regra vertical em todos os tipos e qualificadores tirados dos dados para nomes repetidos. Resultado: 16 tipos, ARI ≥ 0,95 entre subamostras. Atlas, análises, figuras e texto refeitos. | `prereg/A11_DRAFT.md` §2, Supplementary Methods |

## 2. Itens do parecer

Estados: **edição** = resolvido por edição; **análise** = resolvido por análise; **já** = já estava resolvido e foi documentado; **parcial**; **autor** = depende do autor.

| Item | Estado | O que mudou | Evidência |
|---|---|---|---|
| R1 imprevisibilidade | análise + edição | Sai "too sparse to detect or forecast". O mês a mês excede o ruído sobretudo no 1% de setores com mais crime (teto de 0,78; o ensemble explica 0,03). Nos outros 99%, o teto fica entre 0,08 e 0,19. O teto limita qualquer previsão, mas não diz o que os dados disponíveis conseguem. | `fenotipo/reconciliacao.json` (`onde_mora`, `ruido_dispersao`) |
| R2 reconciliação | análise | 20 imputações multinomiais: as taxas, o D² e a persistência não mudam. O R² da média histórica cai de 0,48 para 0,39 com imputação. A ocultação de coordenadas mostra que a reconciliação recupera onde está o crime (r = 0,99), mas tira 13% da variância mensal; por isso tetos e rejeições são conservadores. Methods agora diz que contagem cada análise usa. | `reconciliacao.json`; ED Fig. 10c |
| R2b escores fracionários | já + erro corrigido | Log score e Brier estavam certos. O CRPS estava errado (seção 1). | `scores.py`, A12 |
| R3 identificação | análise | O condicionamento é bom (6,2). Simulações com taxas conhecidas recuperam a ordem das classes (ρ mediano 0,95), mas não as taxas absolutas sob risco por distrito (erro mediano de 33%). O texto passa a interpretar ordens e partes. Trocar testada por área mantém o ranking (ρ de 0,97 a 0,98). | `fenotipo/identificacao.json`; ED Fig. 10a |
| R3b unidades | edição | "Four orders of magnitude" saiu; entre as classes por km com IC longe de zero, a diferença é de duas ordens. | `identificacao.json` (`unidades`) |
| R4 validação | análise + edição | Com metades disjuntas de eventos (ajuste numa, checagem na outra), ρ = 0,83, igual ao original. O resumo diz "consistent with geocoded events…, also with disjoint halves". | `identificacao.json` (`metades`); ED Fig. 10b |
| R5 pedestres | análise (OD 2023 baixada com autorização) | A OD 2023 é a pesquisa principal e a 2017 fica como sensibilidade. Bootstrap de 1.000 réplicas por domicílio. O "19× às 3h" sai e entra o bloco de 0h a 6h: 4,6× (IC 4,2–5,1). A bicicleta é 2,7% e não muda nada. O Methods agora descreve o que o código calcula. | `presenca_2023/presenca_2023.json` |
| R6 negócios | análise + edição | Refeito com os setores certos e só na exploração: IC entre −7% e +8% nas seis variantes, com poder de 80% para efeitos de 5% a 9%. "Not a lever" saiu. O estimador é descrito como DiD contra nunca tratados, com detalhes no SI. | `perturbacao/evento_estudo.json`; ED Fig. 3 |
| R7 confirmação e cronologia | parcial | Cronologia verificável (Tabela S2). Agora estão declarados a exposição de 2026 por distrito no site, o cofre sorteado depois do benchmark, as afirmações escolhidas depois da exploração, a tipagem refeita depois dos resultados e a exposição do evento-estudo ao cofre. **A confirmação não foi rodada:** depende de você datar a A11. | Methods, Tabela S2 |
| R8 teste de dispersão | análise | O nulo calibrado pelo pipeline rejeita 1,7% (2,2% nos setores com ≥ 1/mês). O observado, 3,9% e 14%, fica acima. "Only 4%" saiu. | `reconciliacao.json` (`calibracao`); ED Fig. 10d |
| R9 "jointly" | edição | "fitted each with the same exposures" | — |
| R10 estabilidade dos tipos finais | análise | Estabilidade relatada para os 16 tipos finais e por tipo (Jaccard no SI). Os tipos comerciais raros são os menos estáveis. | `identificacao.json` (`tipos`), Supplementary Methods |
| R11 queda "espalhada" | análise + edição | Em termos absolutos, a queda acompanhou o roubo: os polos tinham 20% do roubo e responderam por 20% da queda. A comparação com Seattle e Boston saiu. Fica o resultado relativo: residenciais 0,40 e polos 1,18. | `ritmo_queda.json`, `robustez.json` |
| R12 favelas | análise | Área, perímetro, domicílios e até um indicador constante dão perfis iguais (ρ ≥ 0,999). Reescalar é inócuo, como o parecer previa. | `identificacao.json` (`favelas`); ED Fig. 10e |
| R13 especificação do benchmark | edição | Tabela S1 completa: modelos, entradas, ajuste, distribuição preditiva e disponibilidade temporal. | SI |
| R14 disponibilidade temporal | já | As covariáveis eram as-of e a tipagem não entrou no benchmark. Documentado, inclusive o snapshot do CNPJ de 2026-09 e o Censo estático. | Methods, Tabela S1 |
| R15 "state" | edição | Definição estatística primeiro; a analogia aparece como rótulo. | Results, Discussion |
| R16 figuras | edição | Fig. 4 reordenada pela força da evidência (o teste pré-especificado vem primeiro). Fig. 6 reduzida a cinco painéis: a violência letal foi para a ED Fig. 5g e o quadro virou a Tabela 1. Nova ED Fig. 10 (robustez). Todos os rótulos em nomes legíveis (pedido seu). | `figures/`, `review/parecer/E_rotulos.md` |
| R17 declarações | **autor** | Autoria, afiliações, ética, financiamento, CRediT, uso de IA, OSF, repositório e DOIs continuam como marcadores. | — |
| R18 literatura | edição | Entraram Stucky & Ottensmann 2009, Quick et al. 2019, De Nadai et al. 2020, Gorr & Lee 2015, Bernasco & Steenbeek 2017, Wu et al. 2022 e Albors Zumel et al. 2026, mais Quick et al. 2018 e Andresen 2007 em Methods. Saiu Andresen 2017, que estava mal colocada. Rotaru 2022 e Varese & Zeng 2024 não entram (justificativa em D). | `review/parecer/D_literatura.md` |
| §4.2–4.7 narrativa | edição | O atlas é o eixo; a previsão aparece como alcance e limite. Laterais reduzidos (o evento-estudo foi para o SI e o ED). A defesa da analogia está num só parágrafo. A mensagem central foi adotada. | — |
| §8 revistas | não implementado | São estimativas subjetivas, e a decisão é sua. | — |

## 3. O que mudou nos resultados (refação completa)

**Mais fortes:**
- D² de 0,44 (era 0,34).
- O relógio do roubo agora se repete nos dois anos (P ≤ 0,005, r = 0,94) e resiste às permutações em blocos.
- O excesso antes do amanhecer em áreas de habitação popular foi confirmado sem modelo (19% contra 5%; continua exploratório).
- A queda: polos 1,18 (IC 1,04–1,32) contra residenciais 0,40.
- O ranking resiste à definição de exposição.

**Mais fracos:**
- Checagem em escala fina: ρ de 0,83 (era 0,93); mediana do painel de 0,78 (era 0,85).
- O "comércio de rua médio" deixou de existir como tipo.
- Ordem das classes dividida por pedestres: ρ = 0,64.

**Achado novo, a investigar:** a violência letal e o roubo de carga estão enriquecidos em casas populares com microempreendedor registrado.

## 4. Pendências

**Feito em 2026-10-27 (sob autorização do autor):**
- A11 (família B, A-R5 exploratória), A12 (CRPS) e A13 (modelos congelados; H4 exploratório) datadas em `prereg/AMENDMENTS.md`; `prereg/selection.json` completo e aplicado.
- 14 modelos de crime, pesos do ensemble, recalibradores do Laya e do comparador do H2 e Markov do destino congelados em `data/models/frozen/` (`cityomics freeze models`).
- **Confirmação única no cofre espacial** (`prereg/atlas_confirmacao.json`, 19 distritos, Holm):
  - A-R1 sustentada: ρ = 0,71 (critério 0,7; margem estreita), P = 0,001;
  - A-R2 sustentada: ρ = 0,54, P = 0,013;
  - A-R6 sustentada: mediana de ρ = 0,85, P < 0,001;
  - A-R7 sustentada: H = 0,17, P = 0,003;
  - **A-R8 não sustentada:** diferença de 0,12 (0,33 na exploração), P = 0,33. A queda mais lenta nos polos continua exploratória e o texto diz isso.
- `freeze.py` em duas etapas (A e B); manuscrito, Tabela 1, limitações e cronologia do SI atualizados; texto principal com 3.493 palavras.

**Congelamento (2026-10-27, o hash dos pesos do Laya veio do Colab depois que o autor restaurou a pasta do Drive):**
- FREEZE-A `25a25cd` (benchmark, modelos, hash do Laya, atlas) e FREEZE-B `cde1bda` (A11–A13 e confirmação). Chave `FREEZE-CDE1BDA` gravada em `prereg/UNSEAL_KEY` (`ca712ae`). O cofre de 2026 continua fechado.
- `model.safetensors` do Laya-FT: sha256 `4c56e1cd…1fa0`. A pasta do Drive não pode mais mudar nem ser apagada; guardar uma cópia.

**Faltam, só do autor:**
1. Preencher as declarações (R17) e decidir a revista.
2. Rodar o H1 em 2026 depois de aberto o cofre (`congelar.prever`) e preencher o último `[CONFIRMATION]`.
3. Registrar no OSF (DOI) e anexar o `ACCESS_LOG`.

**Técnicas, fora desta rodada:**
- Modelo hierárquico da sobredispersão mensal.
- `figures/legends.py` e o explorador já usam a tipagem nova.
- O Laya-FT foi ajustado só em 2024-H1, com soft cross-entropy (não RLCD em 2022–2024); a A13 corrige o texto do protocolo.

## 5. Prontidão

Ainda **não está pronto para submissão.** Faltam a confirmação no cofre e as declarações, e algumas afirmações ainda dependem dela. Como versão de desenvolvimento, o texto está dentro dos limites da Nature Cities (resumo 149, texto 3.492, Methods 2.997, 49 referências no texto principal), e os números conferem com os dados.

## 6. Verificação independente (Agente F, `review/parecer/F_verificacao.md`) e correções aplicadas

Foram conferidos cerca de 150 números. Saíram 26 divergências, nenhuma que invertesse um achado, além de 11 problemas de coerência e 13 exageros. Todas as divergências e todos os exageros foram corrigidos, exceto o item d10, que ficou para a lista técnica.

**Mais importantes:**
- **Casas populares com e sem negócio registrado:** a separação entre os dois tipos não é identificada (exposições com r = 0,85). A violência letal e a carga agora são relatadas para os tipos populares juntos (+1,8 e +1,7), e o ponto entrou nas Limitations.
- **Efeito de distrito:** o texto agora diz que a classe do topo muda e que, sob risco de distrito, o ranking recuperado cai para ρ = 0,84 e a cobertura dos intervalos falha.
- **Queda:** "residenciais" passou a excluir as favelas (0,27, IC 0,05–0,64). O grupo de estações inclui os terminais.
- **Pré-amanhecer:** a checagem sem modelo dá metade da magnitude do modelo. A sugestão de política virou condicional ("if confirmed").
- **Previsão:** "operational value" saiu; ficou "o que a previsão oferece para sinalizar lugares", com o qualificador "in development".
- **Números dos Methods e do SI:** 15.929 setores, termo cruzado de −11%, 17 clusters e 2 fundidos, domínios com k = 7, ARI dos tipos finais de 0,98, tabela de Jaccard refeita a partir do JSON atual.

**Decisões registradas:**
- A auditoria de renda continua como Fig. 6e, e não foi para o Extended Data.
- No evento-estudo vale a versão de `perturbacao/evento_estudo.json` (IC de −7% a +8%), a mesma da ED Fig. 3.

**Ficou para depois:** a sensibilidade da ordem por pedestre a σ com a OD 2023. Com a 2017, ρ varia de 0,49 a 0,81.

**Estado final:**
- resumo: 148 palavras;
- texto principal: 3.499;
- Methods: 2.976;
- 49 referências no texto principal;
- 157 testes passam;
- PDF de leitura com 35 páginas.
