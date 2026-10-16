# Spec — Explorador interativo do CityOmics (Vitessce)

> Parte de [spec-overview.md](spec-overview.md). Lê os objetos do atlas ([spec-atlas.md](spec-atlas.md)) e as previsões do benchmark. Segue a política visual e ética de [spec-figuras.md](spec-figuras.md).

**Em resumo:** a cidade aberta num visualizador de transcriptômica espacial (D48). Os lotes aparecem como pontos coloridos por tipo, em WebGL. Mapa, UMAP, heatmap de marcadores e conjuntos (tipos, domínios) ficam ligados: um clique num tipo destaca as mesmas células em todas as visões.

Há duas versões:
- **local:** inclui o risco previsto por setor;
- **pública:** risco só por distrito ou suavizado por BYM2 (D49, D60). Vira o recurso aberto do artigo.

## 1. Objetos de dados

| Objeto | Linhas | Conteúdo | Versão |
|---|---|---|---|
| `lotes.zarr` (AnnData) | ~1,65 milhão de lotes + pseudo-células FCU | X = genes do lote (sem MEI na versão pública); obs = tipo, domínio, setor, distrito; obsm = `spatial` (centróide em EPSG:31983, em km a partir da origem) e `umap` | local e pública (lista branca) |
| `setores.zarr` (AnnData) | 27.301 spots | composição de tipos, domínio, genes do setor (painel 2025); crime observado de 2025, risco previsto, incerteza | crime e risco só na local |
| `distritos.json` | 96 | agregados: crime observado, risco previsto suavizado, desempenho | local e pública |

Os lotes fora da subamostra do UMAP herdam a coordenada do vizinho mais próximo no espaço PCA, com um leve deslocamento aleatório. O Vitessce ainda não lê polígonos do AnnData (issue 1835). Por isso, lotes e setores aparecem como pontos e spots.

## 2. Visões (configuração do Vitessce)

1. Mapa espacial dos lotes, colorido por tipo (paleta de `viz/palette.py`), com camadas alternáveis: domínio, gene escolhido, risco do setor (local).
2. UMAP dos lotes.
3. Heatmap marcador × tipo.
4. Conjuntos de células: tipos e domínios.
5. Lista de genes, que ao clicar colore o mapa pela expressão.
6. Painel de descrição com as equivalências tecido ↔ cidade e os links para o artigo.

## 3. Construção e hospedagem

- `src/cityomics/explorer/build.py` gera `explorer/local/` e `explorer/public/` (configuração JSON + zarr) com `vitessce` (Python), fixado no lock (D62).
- **Local:** servidor estático (`python -m http.server`), declarado em `.claude/launch.json`.
- **Publicação:** a pasta pública vai para uma hospedagem estática (GitHub Pages ou Zenodo + visualizador), decidida pelo autor na submissão.
- **Git:** as duas pastas ficam fora do git (`.gitignore`). O código e a configuração-modelo são versionados.

## 4. Ética e privacidade

- A versão pública é montada por **lista branca** de colunas, com uma checagem automática que falha se aparecer:
  - risco ou crime por setor;
  - MEI;
  - `nm_fcu`;
  - nomes de bairros;
  - camadas de crime por lote.
- Nenhum ponto de crime. Nenhum dado de 2026 antes do FREEZE.
- `cityomics privacy-scan` cobre `*.zarr`, `*.json` e `*.h5ad` (D60).

## 5. Testes

- Um script abre a configuração pública e confere a lista branca.
- Os tamanhos do zarr ficam abaixo de limites razoáveis para hospedagem estática.
- Teste manual no navegador do app: o mapa carrega, o clique num tipo destaca as células no UMAP e no heatmap.

## Decisions Log

| ID | Topic | Decision | Rationale | Source | Date |
|---|---|---|---|---|---|
| D48 | Interativo | Explorador Vitessce sobre o AnnData do atlas: local agora, recurso aberto (estático) na publicação | Visualizador nativo de transcriptômica espacial; coerente com a analogia | Interview | 2026-10-16 |
| D49 | Ética do explorador | Público: risco só por distrito ou BYM2; setor só local e sob pedido; sem nomes; sem pontos | D11; risco de estigma e de policiamento direcionado | Interview | 2026-10-16 |
| D60 | Coerência de privacidade | Objeto público por lista branca (sem MEI por lote, sem `nm_fcu`, sem crime por lote); scanner estendido; `.gitignore` com `*.zarr` e `explorer/` | Os formatos novos escapavam do scanner | Red Team | 2026-10-16 |
| D62 | Dependências | `vitessce` fixado no lock do ambiente `cityomics` | Reprodutibilidade do recurso aberto | Red Team | 2026-10-16 |

## Dependency Graph & Implementation Order

```
atlas/typing + atlas/spots + atlas/niches ─► explorer/build (lotes.zarr, setores.zarr, distritos.json)
benchmark (pred_dev_eval) ─────────────────┘        ├─► explorer/local/  (com risco por setor)
                                                     └─► explorer/public/ (lista branca, D49/D60)
```

1. Instalar e fixar o `vitessce`.
2. `build.py` com a versão local; testar no navegador.
3. A versão pública com lista branca e o teste automático.
