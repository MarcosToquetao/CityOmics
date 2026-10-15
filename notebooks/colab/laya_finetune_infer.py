"""Laya no Colab: fine-tuning (RLCD) e inferência sobre estados anonimizados (D24, D30).

Este arquivo é o conteúdo das células do notebook ``laya_finetune_infer.ipynb`` (uma célula por bloco
``# %%``). É fino de propósito: só instala o ``laya`` (PyPI) e chama ``laya.train.finetune`` e
``agent.predict_batch``. Sobem ao Colab apenas ``train.jsonl`` e ``score_*.jsonl`` (textos de estado com
ID anônimo); nenhum microdado, endereço, coordenada ou código de setor sai da máquina local.

Gere os arquivos localmente com ``cityomics laya export`` e rode ``cityomics privacy-scan`` antes de subir.
"""

# %% [markdown]
# ## 0. Ambiente (GPU: Runtime > Change runtime type > T4 ou A100)

# %%
!pip install -q laya
import torch, json, hashlib
print(torch.__version__, torch.cuda.get_device_name(0))

# %% [markdown]
# ## 1. Dados anonimizados (envie train.jsonl e score_*.jsonl pelo painel de arquivos do Colab)

# %%
from pathlib import Path
DATA = Path("/content")
print(sorted(p.name for p in DATA.glob("*.jsonl")))
print(open(DATA / "train.jsonl").readline()[:600])

# %% [markdown]
# ## 2. Fine-tuning completo com RLCD (laya-typed-decisions como base)
# 421M parâmetros, contexto 1024, `laya.train.finetune` ajusta também as temperaturas por tipo.

# %%
from huggingface_hub import snapshot_download
from laya.agent import _fix_tokenizer_config
from laya.train import TrainConfig, finetune

BASE = "convaiinnovations/laya-typed-decisions"   # D24: checkpoint typed-decisions (ModernBERT-large, contexto 1024)
model_dir = snapshot_download(BASE, local_dir="/content/laya_base")
_fix_tokenizer_config(model_dir)
cfg = TrainConfig(epochs=3, micro_batch=4, grad_accum=8, calib_max=2000, seed=42, max_len=1024, head_max_len=256,
                  gradient_checkpointing=True, amp=True)
summary = finetune(data=str(DATA / "train.jsonl"), model_dir=model_dir, output_dir="/content/laya_cityomics", config=cfg, device="cuda")
print(summary["temperature"], summary["train_items"], summary["calibration_items"])

# %% [markdown]
# ## 3. Inferência: P(≥1), P(≥3) e faixa de contagem por estado
# Zero-shot (modelo-base) e fine-tuned, com a mesma função. Cada resposta volta com o `state_id` do estado.

# %%
import laya, pandas as pd

QUESTIONS = json.loads(open(DATA / "train.jsonl").readline())["questions"]

def infer(model_path, jsonl, out_csv, batch_size=64):
    agent = laya.load(model_path)
    rows = [json.loads(l) for l in open(jsonl)]
    res = agent.predict_batch([r["state"] for r in rows], QUESTIONS, batch_size=batch_size, sort_by_length=True)
    out = pd.DataFrame({
        "state_id": [r["state_id"] for r in rows],
        "p_ge1": [x["answers"]["ge1"]["noul"] for x in res],
        "p_ge3": [x["answers"]["ge3"]["noul"] for x in res],
        "band_score": [x["answers"]["band"]["score"] for x in res],
    })
    out.to_csv(out_csv, index=False)
    return out

for name in ["recal", "eval"]:
    f = DATA / f"score_{name}.jsonl"
    if f.exists():
        infer("/content/laya_cityomics", f, f"/content/laya_ft_{name}.csv")
        infer(model_dir, f, f"/content/laya_zs_{name}.csv")   # referência zero-shot

# %% [markdown]
# ## 4. Baixar as saídas (probabilidades por state_id) e o hash dos pesos

# %%
h = hashlib.sha256(open("/content/laya_cityomics/model.safetensors", "rb").read()).hexdigest()
print("sha256 dos pesos ajustados:", h)
from google.colab import files
for p in Path("/content").glob("laya_*_*.csv"):
    files.download(str(p))
