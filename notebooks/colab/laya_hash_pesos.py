"""Hash dos pesos ajustados do Laya para o FREEZE-A (prereg §5.2; D24).

Os pesos com fine-tuning ficam no Drive do autor (``/content/drive/MyDrive/laya_cityomics``) e não
entram no repositório. Este roteiro calcula o sha256 de cada arquivo da pasta (pesos, configuração,
tokenizador) e baixa ``pesos_sha256.json``. Copie esse arquivo para
``data/models/frozen/laya_ft/pesos_sha256.json``: o ``cityomics freeze check`` exige esse arquivo, e o hash dele
entra no manifesto. Não sobe nem lê dados. Depois do congelamento, a pasta do Drive não pode mudar.
"""

# %% [markdown]
# ## 1. Montar o Drive

# %%
import hashlib, json, time
from pathlib import Path
from google.colab import drive
drive.mount("/content/drive")
OUT = Path("/content/drive/MyDrive/laya_cityomics")
assert (OUT / "model.safetensors").exists(), f"pesos não encontrados em {OUT}"

# %% [markdown]
# ## 2. sha256 de cada arquivo e download

# %%
def sha256(p, bloco=1 << 24):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(bloco), b""):
            h.update(b)
    return h.hexdigest()

arquivos = {str(p.relative_to(OUT)): {"sha256": sha256(p), "bytes": p.stat().st_size}
            for p in sorted(OUT.rglob("*")) if p.is_file()}
rep = {"pasta_drive": str(OUT), "base": "convaiinnovations/laya-typed-decisions", "calculado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "model_safetensors": arquivos["model.safetensors"]["sha256"], "arquivos": arquivos}
Path("/content/pesos_sha256.json").write_text(json.dumps(rep, indent=2))
print(json.dumps(rep, indent=2))
from google.colab import files
files.download("/content/pesos_sha256.json")
