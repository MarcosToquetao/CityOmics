# Plano de ação: parecer crítico de 2026-10-20

**Fonte:** `~/Downloads/relatorio_critico_plano_revisao_claude (1).md`, sobre `manuscript_figuras.pdf` (24 páginas).

**Como o parecer foi tratado:** como hipóteses de problema, não como erros confirmados. Cada item foi conferido no código e no texto antes da triagem abaixo.

**Rótulos do veredito:**

| Rótulo | Quando se aplica |
|---|---|
| **implementar** | O item procede e cabe nesta rodada. |
| **parcial** | Procede em parte. A justificativa diz qual parte. |
| **já resolvido** | O material já existe e só falta documentar. |
| **não implementar** | Discordância justificada. |
| **autor** | Só o autor pode resolver. |

## 1. Triagem

| Item | O que o parecer pede | Veredito | Por quê | Quem faz |
|---|---|---|---|---|
| R1 | Não inferir imprevisibilidade do fracasso dos modelos | **implementar** | O R² dentro do setor é 0,018, contra um teto de 0,56: mostra que *os modelos testados* não capturam a variação, não que ela é imprevisível. "Too sparse to detect or forecast" (resumo, introdução, discussão) excede a evidência. O teto de 0,56 é agregado e dominado pelos setores de contagem alta. | Texto (eu) + Agente A |
| R2 | A reconciliação faz parte da mensuração; propagar a incerteza | **implementar** | Confirmado no código (`units/reconcile.py`): os eventos sem coordenada são repartidos pela média dos 12 meses anteriores. Isso injeta histórico no desfecho, favorece a média histórica e suaviza a variância mensal. As contagens fracionárias não são realizações de Poisson. | Agente A |
| R2b | Escores com desfecho fracionário | **já resolvido** | `eval/scores.py` trata os três escores: o CRPS vale para y real, o log score usa y arredondado e o evento do Brier é y ≥ 0,5. Falta dizer isso em Methods. | Texto |
| R3 | Separar classes correlacionadas (identificação) | **implementar** | O efeito de distrito não testa identificação. Serão feitos condicionamento de E, simulação com λ conhecido sobre a E real e correlações entre as estimativas no bootstrap. | Agente B |
| R3b | Não comparar taxas por estação e por km | **implementar** | "Four orders of magnitude" mistura unidades. | Texto |
| R4 | Validação sem confundir concordância com independência | **implementar** | O resumo diz "reproduced by geocoded events", sem a ressalva. Serão feitos dois testes: divisão dos eventos geocodificados em metades (ajuste e checagem com eventos disjuntos) e ocultação de coordenadas conhecidas para medir quanto a reconciliação recupera. | Texto + Agentes A e B |
| R5 | OD 2023 e incerteza do pico de 19× às 03h | **parcial** | A incerteza (bootstrap da amostra da OD), a separação entre a pé e bicicleta e a sensibilidade a σ ficam com o Agente C, com os dados locais. A OD 2023 existe (zip de 198 MB, publicado em 2025-02-12), mas a página só a chama de "anexos" e não confirma microdados com coordenadas. Baixar exige autorização explícita: pergunta ao autor. | Agente C + autor |
| R6 | Abertura e fechamento de negócios: "sem efeito detectado" ≠ "sem efeito" | **implementar** | O intervalo de −14% a +5% não exclui reduções relevantes. "Not a lever within a year" (discussão) é forte demais. O estimador é uma diferença em diferenças contra nunca tratados, não o de Callaway–Sant'Anna. Faltam o número de tratados e o tratamento de repetições. O tema vai para o Extended Data, com uma frase no texto principal. | Texto + Agente C |
| R7 | Concluir a confirmação e documentar a cronologia | **parcial** | Documentar a cronologia (datas verificáveis no git e em `prereg/`) e a relação entre o hold-out de 2026 e a janela prospectiva: sim. **Rodar a confirmação: não.** Pelo protocolo, ela só roda depois de o autor datar a A11, e rodá-la agora quebraria o pré-registro. | Texto + autor |
| R8 | Calibrar o teste de dispersão | **implementar** | Rejeitar em 4% com α = 5% é compatível com nenhum excesso, porque o χ² é conservador em contagens baixas. Calibrar o nulo por simulação de Poisson nas médias observadas e com reconciliação. | Agente A |
| R9 | "Jointly fitted" | **implementar** | Methods já diz que a verossimilhança fatoriza. Results ainda diz "fitted them jointly". | Texto |
| R10 | Estabilidade dos 12 tipos finais | **implementar** | O ARI de 0,973 é dos 14 clusters antes do refinamento. Recalcular aplicando as regras de fusão e de separação vertical às subamostras. | Agente B |
| R11 | Queda "espalhada pelo tecido residencial" | **implementar** | A queda por classe não diz se veio de muitos ou de poucos lugares. Medir a concentração da queda entre setores. Se não sustentar, reescrever a frase e tirar a comparação com Seattle e Boston. | Agente C |
| R12 | Exposição das favelas | **implementar** | O parecer acerta: multiplicar a exposição por uma constante só reescala λ, e a participação não muda (a estimativa é invariante a reescalar uma coluna). Testar alternativas que mudam a distribuição espacial: área, perímetro e domicílios^0,5. Fecha uma pendência declarada nas limitações. | Agente B |
| R13 | Especificação do benchmark | **implementar** | Tabela suplementar com modelo, entradas, ajuste, distribuição preditiva e janela. | Agente C |
| R14 | Disponibilidade temporal das covariáveis | **já resolvido** | `covariates/asof.py` desloca cada fonte pela sua defasagem e o CNPJ é reconstruído por data. A tipagem de 2025 não entrou no benchmark (rodado antes do atlas). Ressalvas a documentar: o Censo 2022 é estático e o CNPJ só tem a situação final. | Texto |
| R15 | "State" como resíduo persistente | **implementar** | Definir primeiro em termos estatísticos ("persistência que a composição observada não explica"), com a analogia em segundo plano. A analogia tipo + estado fica, por decisão anterior do autor. | Texto |
| R16 | Figuras 4 e 6 | **implementar** | Fig. 4: abrir pelo teste pré-especificado (furto de celular), com o roubo depois, marcado como exploratório. Fig. 6: manter captura, teto, concentração do excesso e benchmark; levar a violência letal e a auditoria de renda ao Extended Data; a tabela de confirmação vira a Tabela 1 (C1–C5, valor na exploração, resultado no cofre pendente). | Agente E (depois das análises) |
| R17 | Declarações | **autor** | Autoria, ética, financiamento, CRediT, uso de IA, DOIs. Nada é inventado. | Autor |
| R18 | Literatura próxima | **implementar** | Verificar os seis trabalhos citados no parecer e citar só os que mudam o posicionamento. O limite é de cerca de 50 referências no texto principal, então entra uma e sai outra. | Agente D |
| §4.2 | Hierarquia: atlas como eixo, previsão como alcance e limite | **implementar** | Reordenar a discussão e o fechamento. | Texto |
| §4.5 | Resultados laterais | **implementar** | Negócios: só Extended Data e uma frase. A camada de linguagem fica numa frase em Methods (era pré-especificada, por isso não pode sumir). A comunicação L–R já está no Extended Data. | Texto |
| §4.6 | Defesa repetida da analogia | **implementar** | Concentrar a discussão da analogia num parágrafo da discussão. Sai da introdução a frase "instrument whose outputs can fail tests". | Texto |
| §4.7 | Mensagem central | **implementar** | Adotar, com a redação ajustada aos resultados novos. | Texto |
| §8 | Revistas e probabilidades | **não implementar** | São estimativas subjetivas, que o próprio parecer pede para não tratar como dados. A revista-alvo (Nature Cities) é decisão do autor. Fica só o registro: a EPB tem limite de 8.000 palavras com referências. | Autor |

## 2. Agentes e entregas

Regras para todos os agentes:

- Python em `/home/MarcosToquetao/miniforge3/envs/cityomics/bin/python`.
- Nada de 2026 (`guard.pre2026`), crime só nos 77 distritos de exploração (`guard.explore_mask`) e nenhum download.
- Cada agente escreve só no próprio módulo, no teste e na saída. Ninguém edita o manuscrito, as figuras nem `cli.py`.
- Nada é commitado.

| Agente | Itens | Módulo / saída | Relatório |
|---|---|---|---|
| A: reconciliação e ruído | R1, R2, R4 (ocultação), R8 | `atlas/reconciliacao.py` → `fenotipo/reconciliacao.json` | `review/parecer/A_reconciliacao.md` |
| B: identificação e validação | R3, R4 (metades), R10, R12, exposição | `atlas/identificacao.py` → `fenotipo/identificacao.json` | `review/parecer/B_identificacao.md` |
| C: ritmo, queda, evento e benchmark | R5 (parcial), R6, R11, R13, permutação em blocos, IC do perfil horário e do fim de semana | `atlas/ritmo_queda.py` → `fenotipo/ritmo_queda.json` | `review/parecer/C_ritmo_queda.md` + `review/parecer/tabela_S1_benchmark.md` |
| D: literatura | R18 | — | `review/parecer/D_literatura.md` |
| E: figuras (depois de A–C) | R16 + Extended Data de robustez | `figures/` | — |
| F: revisão independente (no fim) | Todos | — | `review/parecer/F_verificacao.md` |

Eu cuido de quatro coisas: as edições de texto que não dependem das análises, a integração dos resultados, o rebuild (md, docx e pdf) e o registro final (`paper/04_registro_parecer.md`).

## 3. Regra de decisão

Se uma análise enfraquecer uma afirmação, a afirmação muda e a história não é preservada à custa da evidência. O registro final diz, item a item, o que foi feito, com que resultado, em que arquivo e o que ficou pendente.
