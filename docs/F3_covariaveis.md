# F3: covariáveis

## Censo 2022 por setor (`covariates/censo.py`)

- **Fonte:** agregados por setor do IBGE, arquivos nacionais filtrados para a capital. Temas: básico, demografia, cor ou raça, alfabetização, domicílio (partes 1 a 3), renda do responsável (liberada em 2026-05-08) e entorno (faces de quadra, domicílios e moradores). Os dicionários oficiais ficam em `data/external/ibge/censo2022/dicionarios/`.
- **Saída:** `data/processed/covariaveis/setor_censo2022.parquet`, com 27.301 setores e 42 indicadores:
  - população, domicílios e densidades;
  - idade e sexo (homens de 15 a 29 anos, 15 a 24, 0 a 14, 60 ou mais, razão de sexo);
  - cor ou raça (branca, preta, parda, negra, amarela);
  - analfabetismo a partir de 15 anos;
  - tipo de domicílio (apartamento, casa, vila ou condomínio, cortiço, estrutura degradada, improvisados);
  - saneamento (água, esgoto, lixo, banheiro, três ou mais banheiros);
  - renda do responsável (média, mediana, coeficiente de variação);
  - entorno, por fração de faces de quadra com: iluminação pública, pavimentação, calçada, obstáculo na calçada, rampa, bueiro, ponto de ônibus, três ou mais árvores, circulação de ônibus e caminhão, circulação só de pedestres.
- **Supressão:** o IBGE suprime células pequenas ("X"). Quando o setor tem total de moradores publicado, uma contagem suprimida vira 0. Isso não vale para médias e variâncias. Setores sem moradores publicados (622, ou 2,3%) ficam ausentes.
- **Tempo:** variável estática de 2022. A renda só foi liberada em maio de 2026, o que é aceitável numa análise retrospectiva (spec-dados §3.3).
