"""Rede neural em grafos espaço-temporal (spec-benchmark §3.2).

Nós = setores; arestas = 8 vizinhos mais próximos por centroide (simétrico). A cada mês, a rede
recebe as features as-of do nó (histórico + núcleo teórico, padronizadas) e propaga informação em
duas camadas de média de vizinhos (GraphSAGE-mean) antes de uma cabeça densa que devolve a média
Poisson. É treinada com a perda de Poisson, um mês por passo (grafo completo), com early stopping
em validação temporal (últimos 3 meses do ajuste). Roda em GPU pequena (4 GB bastam).
"""

from __future__ import annotations

import numpy as np
import polars as pl
import torch
from torch import nn


def norm_adj(idx: np.ndarray, n: int) -> torch.Tensor:
    """Matriz esparsa de média sobre os vizinhos (linha-normalizada), com o próprio nó incluído."""
    k = idx.shape[1]
    rows = np.repeat(np.arange(n), k)
    cols = idx.reshape(-1)
    a = torch.sparse_coo_tensor(np.vstack([rows, cols]), np.ones(len(rows), dtype="float32"), (n, n)).coalesce()
    deg = torch.sparse.sum(a, dim=1).to_dense()
    vals = a.values() / deg[a.indices()[0]]
    return torch.sparse_coo_tensor(a.indices(), vals, (n, n)).coalesce()


class Net(nn.Module):
    def __init__(self, d_in: int, h: int = 96):
        super().__init__()
        self.l1 = nn.Linear(2 * d_in, h)
        self.l2 = nn.Linear(2 * h, h)
        self.head = nn.Sequential(nn.Linear(h, h), nn.ReLU(), nn.Linear(h, 1))

    def forward(self, x, a):
        h = torch.relu(self.l1(torch.cat([x, torch.sparse.mm(a, x)], 1)))
        h = torch.relu(self.l2(torch.cat([h, torch.sparse.mm(a, h)], 1)))
        return nn.functional.softplus(self.head(h).squeeze(-1)) + 1e-4


class GNN:
    def __init__(self, feats: list[str], idx: np.ndarray, device: str | None = None, seed: int = 0):
        self.feats, self.idx, self.seed = feats, idx, seed
        self.dev = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def _tensor(self, df: pl.DataFrame):
        """Lista de (x[n,d], y[n]) por mês, na ordem de setor; exige todos os setores em cada mês."""
        meses = sorted(df["mes"].unique().to_list())
        xs, ys = [], []
        for m in meses:
            d = df.filter(pl.col("mes") == m).sort("cd_setor")
            x = d.select(self.feats).to_numpy().astype("float32")
            x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
            x = np.sign(x) * np.log1p(np.abs(x))
            xs.append(x)
            ys.append(d["y"].to_numpy().astype("float32") if "y" in d.columns else None)
        return meses, xs, ys

    def fit(self, df: pl.DataFrame, epochs: int = 80, lr: float = 2e-3, log=print):
        torch.manual_seed(self.seed)
        meses, xs, ys = self._tensor(df)
        n = xs[0].shape[0]
        allx = np.concatenate(xs)
        self.mu, self.sd = allx.mean(0), allx.std(0) + 1e-6
        X = [torch.tensor((x - self.mu) / self.sd, device=self.dev) for x in xs]
        Y = [torch.tensor(y, device=self.dev) for y in ys]
        self.a = norm_adj(self.idx, n).to(self.dev)
        self.net = Net(X[0].shape[1]).to(self.dev)
        opt = torch.optim.Adam(self.net.parameters(), lr=lr, weight_decay=1e-5)
        tr, va = list(range(len(X) - 3)), list(range(len(X) - 3, len(X)))
        best, bad, state = np.inf, 0, None
        for ep in range(epochs):
            self.net.train()
            for i in np.random.default_rng(ep).permutation(tr):
                opt.zero_grad()
                lam = self.net(X[i], self.a)
                loss = (lam - Y[i] * torch.log(lam)).mean()
                loss.backward()
                opt.step()
            self.net.eval()
            with torch.no_grad():
                v = np.mean([(lambda l: (l - Y[i] * torch.log(l)).mean().item())(self.net(X[i], self.a)) for i in va])
            if v < best - 1e-5:
                best, bad, state = v, 0, {k: t.clone() for k, t in self.net.state_dict().items()}
            else:
                bad += 1
                if bad >= 8:
                    break
        self.net.load_state_dict(state)
        log(f"GNN: {ep + 1} épocas, perda de validação {best:.5f}")
        return self

    def predict(self, df: pl.DataFrame) -> np.ndarray:
        """Previsões na mesma ordem de ``df`` (mês, depois setor): ordene ``df`` por (mes, cd_setor) antes."""
        meses, xs, _ = self._tensor(df)
        out = []
        self.net.eval()
        with torch.no_grad():
            for x in xs:
                out.append(self.net(torch.tensor((x - self.mu) / self.sd, device=self.dev), self.a).cpu().numpy())
        return np.concatenate(out).astype("float64")
