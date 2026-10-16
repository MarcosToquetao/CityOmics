"""Retomada da inferência do Laya no Colab depois que o kernel foi reiniciado (D30).

O treino completo grava os pesos ajustados no Drive (``/content/drive/MyDrive/laya_cityomics``); o que
se perde num reinício é o ambiente (pacotes, ``/content``). Este roteiro reinstala o ``laya``, monta o
Drive, confere os pesos e roda só a inferência. Os CSVs também são gravados no Drive, para não se
perderem de novo. Sobem ao Colab apenas ``score_recal.jsonl`` e ``score_eval.jsonl`` (estados com ID anônimo).
"""

# %% [markdown]
# ## 0. Ambiente e Drive

# %%
!pip install -q laya
import json, hashlib
from pathlib import Path
from google.colab import drive
drive.mount("/content/drive")
OUT = "/content/drive/MyDrive/laya_cityomics"
print(sorted(p.name for p in Path(OUT).glob("*")))   # precisa conter model.safetensors e rl_agent_config.json

# %% [markdown]
# ## 1. Estados anonimizados (envie score_recal.jsonl e score_eval.jsonl para /content)

# %%
DATA = Path("/content")
print(sorted(p.name for p in DATA.glob("*.jsonl")))
faltam = [n for n in ("score_recal.jsonl", "score_eval.jsonl") if not (DATA / n).exists()]
assert not faltam, f"suba para /content: {faltam}"

# %% [markdown]
# ## 2. Inferência (modelo ajustado e zero-shot), com saída no Drive

# %%
import laya, pandas as pd
from huggingface_hub import snapshot_download
from laya.agent import _fix_tokenizer_config

QUESTIONS = {
    "ge1": {"type": "noul", "instructions": "Will at least one cellphone robbery or theft be recorded in this census tract during the forecast month?"},
    "ge3": {"type": "noul", "instructions": "Will three or more cellphone robberies or thefts be recorded in this census tract during the forecast month?"},
    "band": {"type": "score", "instructions": "How many cellphone robberies or thefts will be recorded in this census tract during the forecast month?",
             "criteria": ["none", "one", "two to three", "four to seven", "eight or more"]},
}
CSV_DIR = Path("/content/drive/MyDrive/laya_cityomics_csv")
CSV_DIR.mkdir(exist_ok=True)

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
    if f.exists() and not (CSV_DIR / f"laya_ft_{name}.csv").exists():
        infer(OUT, f, CSV_DIR / f"laya_ft_{name}.csv")
        print("pronto", name, "ajustado")

# %% [markdown]
# ## 3. Referência zero-shot (modelo-base) e hash dos pesos

# %%
base = snapshot_download("convaiinnovations/laya-typed-decisions", local_dir="/content/laya_base")
_fix_tokenizer_config(base)
for name in ["recal", "eval"]:
    f = DATA / f"score_{name}.jsonl"
    if f.exists() and not (CSV_DIR / f"laya_zs_{name}.csv").exists():
        infer(base, f, CSV_DIR / f"laya_zs_{name}.csv")
        print("pronto", name, "zero-shot")
print("sha256 dos pesos ajustados:", hashlib.sha256(open(f"{OUT}/model.safetensors", "rb").read()).hexdigest())

# %% [markdown]
# ## 4. Baixar os CSVs

# %%
from google.colab import files
for p in sorted(CSV_DIR.glob("laya_*_*.csv")):
    files.download(str(p))
