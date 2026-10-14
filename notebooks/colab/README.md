# Notebooks do Colab

Tudo o que depende de GPU roda aqui (D30): fine-tuning e inferência do Laya, scVI, encoders de imagem, Chronos/TimesFM e GNN.

## Regras

1. **Notebooks finos.** Cada notebook só instala o pacote e chama funções dele:
   ```
   !pip install "cityomics[laya] @ git+https://github.com/MarcosToquetao/CityOmics.git"
   ```
   O repositório é privado, então a instalação no Colab precisa de um token do GitHub guardado nos *Secrets* do Colab. Nunca cole o token numa célula.
2. **Só sobem dados de `data/processed/`.** São matrizes agregadas por lote, setor ou distrito e estados serializados com IDs anônimos. Antes de subir, rode `cityomics privacy-scan`.
3. **Nunca sobem:** `data/raw/`, `data/interim/`, `data/sealed_2026/`, `NUM_BO`, logradouro, coordenadas brutas ou chaves.
4. **Saídas** (pesos ajustados, previsões, probabilidades) voltam para `data/processed/` com o hash do modelo e do estado de entrada.
