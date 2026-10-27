# Registro da revisão (2026-10-20)

**Painel:** cinco revisores simulados, cada um em contexto separado (`review/eic.md`, `r1_metodologia.md`, `r2_dominio.md`, `r3_perspectiva.md`, `da.md`). Decisão editorial em `review/decisao_editorial.md`: **revisão maior**, com 133 itens no roteiro. A crítica crítica do advogado do diabo foi validada: a composição "fixava" o crime, mas a persistência do lugar pesa mais. Duas rodadas de correção (o máximo da skill), seguidas de uma revisão de verificação (`review/rereview.md`).

**Decisões do autor:**
- Escopo: texto, figuras e seis análises novas.
- Título mantido: "Crime as a phenotype of urban tissue".

## O que mudou no artigo

1. **Tese estreitada.** A composição estrutura *que* crime e *a que hora*; um efeito persistente do lugar, além da composição, explica mais de *quanto*. O título passou a ser defendido pela analogia completa: fenótipo = tipo (composição) + estado (efeito persistente). Saíram "fixa", "memória" e "o mês a mês é ruído".
2. **Atribuição posicionada como o que é.** É regressão ecológica de Poisson com exposições conhecidas (Goodman). O análogo exato na ômica é o csSAM/CIBERSORTx com composição conhecida. A validação pontual virou "checagem de consistência em escala mais fina", não teste independente.
3. **Relógio.** A abertura agora é o furto de celular, que é a afirmação pré-especificada. O roubo é exploratório (P = 0,07 em 2025). O "41%" saiu porque era um número do modelo; entrou a contagem sem modelo, 16% (IC 12–21%) contra 6%. A vigilância passou a ser uma interpretação compatível, com as alternativas nomeadas.
4. **Mês a mês.** "Esparso e difícil de prever, não ausente". A concentração nos polos é a esperada pela escala (88% esperado contra 86% observado). O teste tem pouco poder. A afirmação vale para crime de celular na escala setor × mês. A analogia é com ruído de medida (Sarkar & Stephens), não com ruído intrínseco nem com o "limite de previsibilidade" de Song.
5. **Escopo de dados explícito em Methods.** O benchmark e a auditoria de renda usaram os 96 distritos, rodados antes da criação do cofre espacial. O ensaio no pseudo-cofre agora é só checagem de código. As afirmações viraram C1–C5, e a H1 foi definida.
6. **Cortes:**
   - camada de linguagem (uma frase só em Methods, porque era pré-especificada);
   - Sankey (Fig. 3f) e ED de teoria;
   - linha ligante–receptor da Fig. 1a.
   
   O benchmark foi reduzido a um parágrafo.
7. **Termos, figuras e referências:**
   - Novo: glossário, tipos de crime nomeados pela definição real, "padrão baixo" no lugar de "baixa renda".
   - Figuras com os mesmos nomes do texto. O Extended Data foi renumerado pela ordem de citação.
   - Ética: novo parágrafo sobre estigma territorial e usos excluídos.
   - Referências: 16 novas, todas com DOI conferido na Crossref, exceto Eck et al. 2007, que não tem DOI.

## As seis análises novas

Arquivo `src/cityomics/atlas/robustez.py`, comando `cityomics atlas run robustez`, saída em `data/processed/atlas/fenotipo/robustez.json`. Só exploração, sem 2026.

| Análise | Resultado | Efeito no texto |
|---|---|---|
| Persistência só com eventos geocodificados | 40% composição, 46% persistente; r = 0,62 em 3 anos | Confirma; entra no texto |
| Queda separada entre furto e roubo | Roubo no residencial de padrão baixo cai mais que a cidade (0,56); comércio médio (1,15) e estações (0,91) não | O padrão sobrevive dentro do roubo |
| Taxas com efeito de distrito | Ordem preservada (ρ = 0,96), mas as taxas centrais caem à metade (comércio médio 70 → 23/km) | Taxas absolutas qualificadas |
| Poder do teste de dispersão | 12% com 0,25 evento/mês e CV = 1 | "96% Poisson" deixa de ser evidência |
| Excesso de variância pela escala | 88% esperado contra 86% observado no 1% do topo | Sai "a dinâmica mora nos polos" |
| Relógio sem modelo | 16% (12–21%) contra 6%; 282 eventos em 313 setores | Sai o "41%" |

## Pendências do autor

1. **A11 (antes de datar):** a revisão sugere apertar critérios e acrescentar variantes.
   - C2 com ρ > 0 é fraco.
   - C4 precisa de permutação em blocos.
   - C5 deve sair também dentro do roubo.
   - O relógio do roubo poderia entrar na família.
   
   Cada mudança é decisão sua; o texto já descreve C5 "também dentro do roubo".
2. **Análises adiadas (declaradas nas limitações):**
   - divisão de eventos geocodificados para validação fora da amostra;
   - permutação em blocos;
   - modelo hierárquico de sobredispersão mensal;
   - sensibilidade da exposição das favelas;
   - teste de escuridão (horário do nascer do sol);
   - ponto de ônibus como classe.
3. **Marcadores no texto:** `[AUTHORS]`, `[CONFIRMATION]`, `[OSF DOI]`, `[ETHICS]`, uso de IA, financiamento, CRediT, repositório e Zenodo.
4. **Legendas antigas:** `figures/legends.py` e `figures/legendas_dev.md` ainda têm as versões anteriores. As legendas válidas estão no manuscrito.
5. **Pendências que a verificação deixou** (`review/rereview.md`, nível de revisão menor):
   - intervalos bootstrap do perfil horário do modelo e da razão de fim de semana;
   - Fig. 5e só com o crime de celular agregado;
   - paleta da Fig. 1 invertida em relação às Figs. 2–5.
