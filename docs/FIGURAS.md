# Figuras do artigo e explorador — como regerar

Spec: [spec-figuras.md](../spec-figuras.md) e [spec-explorer.md](../spec-explorer.md). Decisões D34–D62.

## Ordem

```bash
cityomics atlas run            # genes → ruas → tipagem → spots → nichos → atribuição → variância → preditores → comunicação → destino → letal
cityomics figures --periodo dev
cityomics explorer             # versão local (com risco por setor; não compartilhar)
cityomics explorer --public    # versão pública por lista branca (D49, D60)
```

- O período `dev` usa a avaliação de 2025.
- O período `2026` só roda com o cofre aberto, depois do FREEZE (D52). Nesse caso, as figuras leem o pacote de resultados congelado.

## Saídas (fora do git)

- `figures/out/<periodo>/figN.pdf` e `.png`:
  - o PDF é vetorial, com as fontes embutidas (Type 42);
  - o PNG tem 450 dpi, para revisão.
- `data/processed/atlas/`: tipos, composições, nichos, atribuição, comunicação, destino.
- `data/processed/figdata/`: tabelas prontas para as figuras (cache; apague para recalcular).
- `explorer/local/` e `explorer/public/`: AnnData em zarr, `config.json` e `index.html`. Para servir:
  ```bash
  python -m http.server 8790 --directory explorer/local
  ```

## Regras que as figuras seguem

- **Padrão Nature (D36):**
  - largura de 89 ou 183 mm;
  - texto de 5 a 7 pt;
  - letras a, b, c em 8 pt e negrito.
- **Fonte:** Arial, ou Liberation Sans quando o Arial não está instalado (D62).
- **Fundo (D45):** mapas em fundo escuro e gráficos em fundo branco.
- **Paleta:** semântica por família de tipo (`viz/palette.py`).
- **Proteção do setor (D60):** nenhum ponto de crime aparece. Os mapas com valores por setor (risco, acerto/erro) saem rasterizados, para que o valor de um setor não possa ser extraído do PDF.
- **Esquema da Fig. 1a:** `figures/assets/fig1a_esquema.svg` é desenhado à mão e sobreposto em vetor (cairosvg + pypdf) ao PDF da Fig. 1. Pode ser refinado no Inkscape sem tocar no código.
- **Exploração com crime no atlas:** exclui os 19 distritos do cofre espacial (`prereg/atlas_vault.json`, D53). A confirmação nesses distritos só roda depois da emenda A11.

## Estado em 2026-10-16 (desenvolvimento)

- **Figuras:** Figs. 1–6 e ED1–ED5 geradas em `figures/out/dev/`, com legendas em `figures/legendas_dev.md`.
- **Explorador:** usa a subamostra aleatória de 150 mil lotes, a mesma do UMAP, com coordenadas exatas. Com 1,6 milhão de pontos e um heatmap de 1,6 milhão de colunas, o navegador travava. O mapa completo está na Fig. 1. As visões de mapa são dispersões das coordenadas (km), porque as visões espaciais do Vitessce 3.9 não colorem pontos por conjunto.
- **Formato dos dados:** zarr v2 com compressão Blosc-LZ4. O zstd que o anndata 0.13 grava não abre no Vitessce.
- **Pendente:**
  - **versão pública:** ainda não mostra o risco por distrito previsto na D49. Hoje ela é mais restritiva, sem nenhum risco;
  - **OD 2017:** ficou fora do multiverso (base não baixada);
  - **GNN:** a ablação de arestas não foi feita.
