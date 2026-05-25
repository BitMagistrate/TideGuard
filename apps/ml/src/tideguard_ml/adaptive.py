"""Adaptive loss-weight balancing for PINN training (TASK-018).

Two strategies are implemented:

* ``ntk_weights`` — Neural-Tangent-Kernel rebalancing à la
  Wang et al. 2022 (https://arxiv.org/abs/2007.14527). At step ``t`` we
  reweight each loss component by ``trace(K_i) / trace(K_total)``, which
  matches the convergence-rate of the slowest term.
* ``grad_norm_weights`` — gradient-norm balancing, the variant most
  commonly used in production PINN libraries (DeepXDE, NVIDIA Modulus).
  Weights are proportional to ``||∇L_total||/||∇L_i||``.

Both functions return a ``dict[str, float]`` keyed by ``data``, ``pde``,
``ic``, ``bc`` so the caller can multiply each loss component directly.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import torch
import torch.nn as nn


def _flat_grad(loss: torch.Tensor, params: list[torch.Tensor]) -> torch.Tensor:
    grads = torch.autograd.grad(loss, params, create_graph=False, retain_graph=True, allow_unused=True)
    flats = []
    for g, p in zip(grads, params):
        if g is None:
            flats.append(torch.zeros_like(p).flatten())
        else:
            flats.append(g.flatten())
    return torch.cat(flats)


def grad_norm_weights(
    model: nn.Module,
    losses: Mapping[str, torch.Tensor],
    smoothing: float = 0.1,
    prev: Mapping[str, float] | None = None,
    max_weight: float = 100.0,
) -> dict[str, float]:
    """Compute per-task loss weights so that gradient norms become equal."""
    params = [p for p in model.parameters() if p.requires_grad]
    norms: dict[str, float] = {}
    for name, loss in losses.items():
        if not loss.requires_grad:
            norms[name] = 1.0
            continue
        g = _flat_grad(loss, params)
        norms[name] = float(g.norm().item()) + 1e-8
    geo = math.exp(sum(math.log(n) for n in norms.values()) / max(len(norms), 1))
    new = {k: min(max_weight, geo / v) for k, v in norms.items()}
    if prev is None:
        return new
    return {k: (1.0 - smoothing) * prev.get(k, 1.0) + smoothing * new[k] for k in new}


def ntk_weights(
    model: nn.Module,
    losses: Mapping[str, torch.Tensor],
    prev: Mapping[str, float] | None = None,
    smoothing: float = 0.1,
    max_weight: float = 100.0,
) -> dict[str, float]:
    """NTK-trace based weight: w_i ∝ 1 / trace(K_i).

    Trace of the NTK is approximated by ``||∇L_i||² / 2L_i``, which is the
    leading-order term of the unbiased estimator used in Wang et al. 2022.
    """
    params = [p for p in model.parameters() if p.requires_grad]
    inv_trace: dict[str, float] = {}
    for name, loss in losses.items():
        if not loss.requires_grad or loss.item() < 1e-12:
            inv_trace[name] = 1.0
            continue
        g = _flat_grad(loss, params)
        trace = float((g.dot(g) / (2.0 * loss.item() + 1e-12)).item()) + 1e-8
        inv_trace[name] = 1.0 / trace
    total = sum(inv_trace.values()) or 1.0
    new = {k: min(max_weight, v * len(inv_trace) / total) for k, v in inv_trace.items()}
    if prev is None:
        return new
    return {k: (1.0 - smoothing) * prev.get(k, 1.0) + smoothing * new[k] for k in new}


__all__ = ["grad_norm_weights", "ntk_weights"]
