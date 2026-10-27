# Plano do artigo: estrutura, argumento e orçamento

A estrutura segue a tese D63 e o mapa de figuras aprovados pelo autor (`docs/NARRATIVA.md` §10; `spec-figuras.md`). A regra de corte foi uma só: entra no texto principal apenas o que sustenta uma das três afirmações (onde/que crime, a que hora, o que sobra para prever). Comunicação L–R, nichos, domínios, multiverso, SHAP e o benchmark completo ficam no Extended Data, citados em uma frase cada.

## Título

**Crime as a phenotype of urban tissue** (36 caracteres; sem verbo nem pontuação, como pede a revista)

## Arco e orçamento de palavras

| Seção | Afirmação (claim) | Evidência | Explicação / ligação | Palavras |
|---|---|---|---|---|
| Introdução, §1 | O crime se concentra em poucos lugares, mas as teorias falam de componentes e de horas, e os dados vêm em agregados misturados | Lei da concentração; atividades rotineiras; geradores e atratores; falácia ecológica; estudos de uso do solo e de hora | Falta um instrumento que leia composição, tipo de crime e ritmo juntos | 220 |
| Introdução, §2 | A transcriptômica espacial resolveu o mesmo problema (spots misturados) e já tem esse instrumento | Deconvolução, matriz-assinatura, programas, nichos, relógio por tecido; metáforas urbanas anteriores | A analogia vale como instrumento testável, não como metáfora | 150 |
| Introdução, §3 | O que fazemos e o que achamos | Desenho (lotes = células, setores = spots); cofre; auditoria contra o análogo urbano | Três perguntas → três resultados | 200 |
| R1 Tecido | A cidade tem um tecido estável e definido sem crime | 12 tipos, ARI 0,973; favelas; nichos e domínios | Base para atribuir | 180 |
| R2 Assinatura | Cada classe tem uma assinatura criminal | Taxas por km; validação pontual 0,93; 15 fenótipos; 11 classes no topo; controle positivo; programas k = 4 | Composição fixa quanto e qual crime | 500 |
| R3 Relógio | Cada classe tem um relógio, que é de vigilância e não de multidão | Permutação e réplica; 41% de madrugada; OD 2017: ranking sobrevive (0,75), relógio ≠ pedestres (0,03), risco por pedestre 19× às 3 h | Atividade rotineira com resolução de lote | 450 |
| R4 Memória e mudança | Tecido estável, lugares que lembram, taxas que se movem | R² tecido 0,25 × história 0,48; 42/48%; r = 0,63 em 3 anos; 98,2%/ano; queda de 20% concentrada na malha difusa; evento-estudo nulo | Composição + memória fixam o "onde"; o crime recuou para os nichos | 430 |
| R5 Limite | O mês a mês é ruído fora dos polos | R² dentro do setor 0,018 de 0,56; 96% Poisson; 88% do excesso no 1%; benchmark +4%, H1b nulo; equidade; pseudo-cofre | Previsão além do mapa rende pouco | 470 |
| Discussão | Implicações para prevenção, previsão e para a analogia; limitações | Hot spots policing; previsão policial e viés; auditoria de equivalências | Fecha a tese | 700 |
| **Total do texto principal** | | | | **≈ 3.300** |
| Methods | 14 subseções curtas | | | ≈ 2.700 |

## Pré-compromisso do redator (Phase 4a, paráfrase do contrato)

- **D1, completude:** todas as seções do plano escritas. Os únicos marcadores permitidos são `[CONFIRMATION]` (resultados que ainda não existem, decisão do autor) e os de autoria e financiamento.
- **D2, densidade de citação:** toda afirmação factual sobre a literatura tem referência verificada. Afirmações sobre os dados têm número e figura. Não afirmamos prioridade ("primeiro").
- **D3, fidelidade ao plano:** cada subseção de Results abre com a afirmação, segue com a evidência e fecha ligando à tese.
- **D4 e D5, palavras:** texto principal ≤ 3.500 e Methods ≤ 3.000; cada seção a até ±15% do orçamento acima.
- **D6, parágrafos:** um ponto por parágrafo, com transição entre seções.
- **D7, registro:** inglês acadêmico da Nature, sem jargão de ômica sem definição. A analogia é explicada uma vez (Fig. 1a) e depois usada com parcimônia.

[PRE-COMMITMENT-ACKNOWLEDGED]

## Decisões de conteúdo (coerência)

- **Termos fixos:**
  - *parcel* (lote), *cell class* (12 tipos + favelas + 3 classes de rua + estações + terminais = 19 classes), *tract* (setor), *tissue* (composição do setor em classes);
  - *phenotype* (tipo de crime);
  - *phone crime* = furto + roubo de celular; *phone theft* = furto; *phone robbery* = roubo.
- **Madrugada:** usamos 41% dos roubos de dias úteis entre 04:00 e 05:59, contra 3,1% dos pedestres na mesma janela (mesma base de dias úteis). A legenda antiga dizia 39%, que é o valor de todos os dias, misturado com pedestres de dias úteis. Corrigido no texto e nas legendas do manuscrito.
- **Poisson:** reportamos 96% de todos os setores e 86% dos setores com ≥ 1 evento por mês. Os setores de contagem baixa têm pouco poder, então a frase não pode se apoiar só no 96%.
- **Pré-registro:** o plano é versionado e ainda não foi registrado no OSF. O texto diz "pre-specified, version-controlled analysis plan" e traz um marcador para o DOI do OSF. Não dizemos "preregistered".
