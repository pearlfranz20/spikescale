"""Multiscale residual VQ tokenizer for binned spike counts.

Design (from the project plan, revised after review):

- Encoder and decoder are pointwise in time (1x1 convs). The only operations
  that move information across time are the level pooling and the
  nearest-neighbour upsampling, so level k can only represent structure at its
  own bin width.
- Level k average-pools the current residual to L_k positions, quantizes each
  position against its own EMA codebook, repeats the result back to T, and adds
  it to the cumulative reconstruction.
- Decoder maps the cumulative reconstruction to a log Poisson rate per unit per
  bin. Loss is Poisson NLL plus commitment.
- Nested dropout keeps only the first k levels on some steps, so coarse levels
  must carry signal on their own.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F

from .synth import LEVEL_LENGTHS


@dataclass
class TokenizerConfig:
    n_units: int
    T: int = 50
    d: int = 32
    hidden: int = 128
    level_lengths: tuple[int, ...] = LEVEL_LENGTHS
    codebook_sizes: tuple[int, ...] = (32, 64, 64, 128, 128, 128)
    ema_decay: float = 0.95
    commit_beta: float = 0.05
    nested_dropout_p: float = 0.5
    restart_every: int = 100  # steps between dead-code checks; codes unused in that window restart
    # Score each level's cumulative reconstruction against counts pooled to that
    # level's length. Without this, 5 ms Poisson noise dominates the gradient
    # and coarse levels learn almost nothing (see notes/diagnostics.md).
    multiscale_loss: bool = True
    # Linear 1x1 encoder: pooling then commutes with encoding, so level k sees a
    # projection of counts pooled at exactly its own timescale.
    linear_encoder: bool = True


class EMACodebook(nn.Module):
    def __init__(self, size: int, dim: int, decay: float, restart_every: int = 100):
        super().__init__()
        self.size, self.dim, self.decay = size, dim, decay
        self.restart_every = restart_every
        self.register_buffer("embed", torch.randn(size, dim) * 0.1)
        self.register_buffer("cluster_size", torch.zeros(size))
        self.register_buffer("embed_sum", self.embed.clone())
        self.register_buffer("initialized", torch.tensor(False))
        self.register_buffer("window_usage", torch.zeros(size))
        self.register_buffer("steps", torch.tensor(0))
        self.restarts = 0

    @torch.no_grad()
    def _kmeans_init(self, x: torch.Tensor):
        idx = torch.randint(0, x.shape[0], (self.size,))
        self.embed.copy_(x[idx])
        self.embed_sum.copy_(self.embed)
        self.cluster_size.fill_(1.0)
        self.initialized.fill_(True)

    def forward(self, x: torch.Tensor):
        """x: (M, dim) -> quantized (M, dim), indices (M,)"""
        if self.training and not bool(self.initialized):
            self._kmeans_init(x.detach())
        dist = (
            x.pow(2).sum(1, keepdim=True)
            - 2 * x @ self.embed.t()
            + self.embed.pow(2).sum(1)[None]
        )
        idx = dist.argmin(1)
        q = self.embed[idx]
        if self.training:
            self._ema_update(x.detach(), idx)
        return q, idx

    @torch.no_grad()
    def _ema_update(self, x, idx):
        onehot = F.one_hot(idx, self.size).type(x.dtype)
        counts = onehot.sum(0)
        self.cluster_size.mul_(self.decay).add_(counts, alpha=1 - self.decay)
        self.embed_sum.mul_(self.decay).add_(onehot.t() @ x, alpha=1 - self.decay)
        n = self.cluster_size.sum()
        smoothed = (self.cluster_size + 1e-5) / (n + self.size * 1e-5) * n
        self.embed.copy_(self.embed_sum / smoothed[:, None])
        # dead-code restart: only codes unused for a whole window of steps
        self.window_usage.add_(counts)
        self.steps.add_(1)
        if int(self.steps) % self.restart_every == 0:
            dead = self.window_usage == 0
            if dead.any():
                k = int(dead.sum())
                pick = x[torch.randint(0, x.shape[0], (k,))]
                self.embed[dead] = pick
                self.embed_sum[dead] = pick * self.cluster_size[~dead].mean()
                self.cluster_size[dead] = self.cluster_size[~dead].mean()
                self.restarts += k
            self.window_usage.zero_()


class MultiscaleRVQ(nn.Module):
    def __init__(self, cfg: TokenizerConfig):
        super().__init__()
        self.cfg = cfg
        assert all(cfg.T % L == 0 for L in cfg.level_lengths)
        if cfg.linear_encoder:
            self.encoder = nn.Conv1d(cfg.n_units, cfg.d, 1)
        else:
            self.encoder = nn.Sequential(
                nn.Conv1d(cfg.n_units, cfg.hidden, 1), nn.GELU(),
                nn.Conv1d(cfg.hidden, cfg.hidden, 1), nn.GELU(),
                nn.Conv1d(cfg.hidden, cfg.d, 1),
            )
        self.decoder = nn.Sequential(
            nn.Conv1d(cfg.d, cfg.hidden, 1), nn.GELU(),
            nn.Conv1d(cfg.hidden, cfg.hidden, 1), nn.GELU(),
            nn.Conv1d(cfg.hidden, cfg.n_units, 1),
        )
        self.codebooks = nn.ModuleList(
            EMACodebook(V, cfg.d, cfg.ema_decay, cfg.restart_every) for V in cfg.codebook_sizes
        )
        # per-unit input standardization, set from training data
        self.register_buffer("in_mean", torch.zeros(1, cfg.n_units, 1))
        self.register_buffer("in_std", torch.ones(1, cfg.n_units, 1))

    @torch.no_grad()
    def fit_input_norm(self, counts: torch.Tensor):
        x = torch.log1p(counts)
        self.in_mean.copy_(x.mean((0, 2), keepdim=True))
        self.in_std.copy_(x.std((0, 2), keepdim=True).clamp_min(1e-3))

    @property
    def K(self) -> int:
        return len(self.cfg.level_lengths)

    def encode(self, counts: torch.Tensor) -> torch.Tensor:
        x = (torch.log1p(counts) - self.in_mean) / self.in_std
        return self.encoder(x)  # (B, d, T)

    def quantize(self, z: torch.Tensor, n_levels: int | None = None, use_vq: bool = True):
        """Residual multiscale quantization.

        Returns cumulative reconstructions after each level (list of (B, d, T)),
        per-level code indices (list of (B, L_k)), per-level pooled targets and
        their quantized values (for the commitment loss).

        With use_vq=False the pooled residuals pass through unquantized. This is
        the continuous multiscale pyramid of z, used for warm-up.
        """
        n_levels = self.K if n_levels is None else n_levels
        B, d, T = z.shape
        zhat = torch.zeros_like(z)
        cumulative, indices, pooled, quantized = [], [], [], []
        for k in range(n_levels):
            L = self.cfg.level_lengths[k]
            resid = z - zhat
            u = F.adaptive_avg_pool1d(resid, L)  # (B, d, L)
            flat = u.permute(0, 2, 1).reshape(-1, d)
            if use_vq:
                q_flat, idx = self.codebooks[k](flat)
            else:
                q_flat, idx = flat, torch.zeros(flat.shape[0], dtype=torch.long)
            q = q_flat.reshape(B, L, d).permute(0, 2, 1)
            zhat = zhat + q.repeat_interleave(T // L, dim=2)  # nearest-neighbour upsample
            cumulative.append(zhat)
            indices.append(idx.reshape(B, L))
            pooled.append(u)
            quantized.append(q)
        return cumulative, indices, pooled, quantized

    def decode(self, zhat: torch.Tensor) -> torch.Tensor:
        return self.decoder(zhat)  # log-rate (B, N, T)

    @torch.no_grad()
    def init_codebooks_kmeans(self, counts: torch.Tensor, seed: int = 0):
        """After warm-up, fit each level's codebook by k-means on its pooled residuals.

        Levels are fit in order, so level k sees residuals left by the already
        quantized levels 1..k-1, exactly as at inference.
        """
        from sklearn.cluster import MiniBatchKMeans

        self.eval()
        z = self.encode(counts)
        B, d, T = z.shape
        zhat = torch.zeros_like(z)
        for k, cb in enumerate(self.codebooks):
            L = self.cfg.level_lengths[k]
            u = F.adaptive_avg_pool1d(z - zhat, L)
            flat = u.permute(0, 2, 1).reshape(-1, d)
            km = MiniBatchKMeans(n_clusters=cb.size, random_state=seed, n_init=3,
                                 batch_size=2048).fit(flat.numpy())
            centers = torch.as_tensor(km.cluster_centers_, dtype=z.dtype)
            cb.embed.copy_(centers)
            cb.cluster_size.fill_(flat.shape[0] / cb.size)
            cb.embed_sum.copy_(centers * cb.cluster_size[:, None])
            cb.initialized.fill_(True)
            q = centers[torch.as_tensor(km.predict(flat.numpy()))].reshape(B, L, d).permute(0, 2, 1)
            zhat = zhat + q.repeat_interleave(T // L, dim=2)

    def forward(self, counts: torch.Tensor, n_levels: int | None = None, use_vq: bool = True):
        z = self.encode(counts)
        cumulative, indices, pooled, quantized = self.quantize(z, n_levels, use_vq)
        commit = sum(F.mse_loss(u, q.detach()) for u, q in zip(pooled, quantized)) / len(pooled)

        if self.cfg.multiscale_loss:
            # each level k is scored on counts pooled to its own length L_k
            terms = []
            for k, zh in enumerate(cumulative):
                L = self.cfg.level_lengths[k]
                rate = torch.exp(self.decode(z + (zh - z).detach()))
                pooled_rate = F.adaptive_avg_pool1d(rate, L) * (self.cfg.T // L)
                pooled_counts = F.adaptive_avg_pool1d(counts, L) * (self.cfg.T // L)
                # no rescaling by bin width: dividing by T // L would shrink the
                # level-1 term 50x and starve the coarse levels of gradient
                terms.append(F.poisson_nll_loss(pooled_rate, pooled_counts, log_input=False,
                                                full=False))
            nll = torch.stack(terms).mean()
        else:
            zhat = cumulative[-1]
            log_rate = self.decode(z + (zhat - z).detach())  # straight-through
            nll = F.poisson_nll_loss(log_rate, counts, log_input=True, full=False)

        loss = nll + self.cfg.commit_beta * commit
        return loss, {"nll": nll.detach(), "commit": commit.detach(), "indices": indices}

    def sample_n_levels(self) -> int:
        if torch.rand(()) < self.cfg.nested_dropout_p:
            return int(torch.randint(1, self.K + 1, ()))
        return self.K

    @torch.no_grad()
    def level_features(self, counts: torch.Tensor) -> list[torch.Tensor]:
        """Code features for decoding: for each k, the cumulative latent pooled to L_k.

        The cumulative latent after level k is piecewise constant on L_k
        segments, so pooling to L_k loses nothing and gives (B, d * L_k).
        """
        self.eval()
        z = self.encode(counts)
        cumulative, _, _, _ = self.quantize(z)
        feats = []
        for k, zh in enumerate(cumulative):
            L = self.cfg.level_lengths[k]
            feats.append(F.adaptive_avg_pool1d(zh, L).flatten(1))
        return feats

    @torch.no_grad()
    def level_nll(self, counts: torch.Tensor) -> list[float]:
        """Held-out Poisson NLL per bin when decoding from the first k levels."""
        self.eval()
        z = self.encode(counts)
        cumulative, _, _, _ = self.quantize(z)
        out = []
        for zh in cumulative:
            lr = self.decode(zh)
            out.append(float(F.poisson_nll_loss(lr, counts, log_input=True, full=True)))
        return out

    @torch.no_grad()
    def code_usage(self, counts: torch.Tensor) -> list[dict]:
        """Per-level unique codes used and perplexity on a dataset."""
        self.eval()
        z = self.encode(counts)
        _, indices, _, _ = self.quantize(z)
        stats = []
        for k, idx in enumerate(indices):
            V = self.cfg.codebook_sizes[k]
            hist = torch.bincount(idx.flatten(), minlength=V).float()
            p = hist / hist.sum()
            nz = p[p > 0]
            ppl = float(torch.exp(-(nz * nz.log()).sum()))
            stats.append({"level": k + 1, "used": int((hist > 0).sum()), "size": V, "perplexity": ppl})
        return stats


def cumulative_bits(cfg: TokenizerConfig) -> list[float]:
    import math
    bits, total = [], 0.0
    for L, V in zip(cfg.level_lengths, cfg.codebook_sizes):
        total += L * math.log2(V)
        bits.append(total)
    return bits


def train_tokenizer(counts, cfg: TokenizerConfig, epochs: int = 120, batch: int = 64,
                    lr: float = 2e-3, seed: int = 0, verbose: bool = False,
                    warmup_epochs: int | None = None) -> MultiscaleRVQ:
    """Train with a continuous warm-up, then k-means codebook init, then VQ.

    warmup_epochs defaults to a third of `epochs`. During warm-up the levels
    pass pooled residuals through unquantized, so the encoder learns the
    multiscale structure before any codebook can collapse it.
    """
    torch.manual_seed(seed)
    model = MultiscaleRVQ(cfg)
    x = torch.as_tensor(counts, dtype=torch.float32)
    model.fit_input_norm(x)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    warmup = epochs // 3 if warmup_epochs is None else warmup_epochs
    n = x.shape[0]
    for ep in range(epochs):
        if ep == warmup:
            model.init_codebooks_kmeans(x, seed)
        use_vq = ep >= warmup
        model.train()
        perm = torch.randperm(n)
        tot = 0.0
        for i in range(0, n, batch):
            xb = x[perm[i:i + batch]]
            loss, info = model(xb, model.sample_n_levels(), use_vq=use_vq)
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot += float(info["nll"]) * len(xb)
        sched.step()
        if verbose and (ep % 20 == 0 or ep == epochs - 1):
            print(f"  epoch {ep:3d} nll {tot / n:.4f}", flush=True)
    model.eval()
    return model
