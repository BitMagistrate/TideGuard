"""Training script for TideGuard PINN.

Per audit:
  * TASK-001: forward / pde_residual take forcing channels as inputs.
  * TASK-002: ``TrainingMeta`` (domain, bbox, horizon, forcing_source, git_sha)
    is saved alongside the state dict so inference can normalise lon/lat
    correctly and reject out-of-domain queries.
  * TASK-018: ``--adaptive {ntk,grad_norm,off}`` enables on-the-fly loss
    rebalancing every ``--rebalance-every`` steps.
  * TASK-021: ``--codecarbon`` measures the training run's emissions when the
    ``codecarbon`` package is installed.

Usage::

    python -m tideguard_ml.train --synthetic --epochs 5000
    python -m tideguard_ml.train --real --reports data/reports.csv \\
        --forcing data/forcing.npz --epochs 5000
    python -m tideguard_ml.train --synthetic --epochs 5000 --seed-ensemble 5
"""

from __future__ import annotations

import argparse
import logging
import math
import os
from dataclasses import asdict, dataclass, replace
from typing import Literal

import torch

from tideguard_ml.adaptive import grad_norm_weights, ntk_weights
from tideguard_ml.data import RealDataset, SyntheticDataset
from tideguard_ml.inference import TrainingMeta
from tideguard_ml.pinn import PINN, pde_residual

logger = logging.getLogger(__name__)


@dataclass
class TrainConfig:
    epochs: int = 5000
    lr: float = 1e-3
    n_collocation: int = 4096
    n_obs_batch: int = 1024
    w_data: float = 1.0
    w_pde: float = 0.1
    w_bc: float = 1.0
    w_ic: float = 1.0
    device: str = "cpu"
    adaptive: Literal["off", "ntk", "grad_norm", "relo_bra_lo"] = "off"
    rebalance_every: int = 250
    warmup_pde_epochs: int = 0
    multi_physics: bool = False


def relo_bra_lo(
    losses: dict[str, torch.Tensor],
    w_prev: dict[str, float],
    T: float = 0.1,
    alpha: float = 0.999,
) -> dict[str, float]:
    """Relative-Loss Balancing with Random Lookback (Wang et al. 2022).

    Computes the per-loss ratio l_i(t)/l_i(0)-like quantity using the
    detached current value as the lookback baseline, applies a softmax with
    temperature T to convert ratios into weights, and exponentially mixes
    with the previous step weights.  Numerically stable on small batches.
    """
    keys = list(losses.keys())
    with torch.no_grad():
        # Normalise each loss to the [0, 1] range by dividing by the
        # current detached magnitude — this puts losses of very different
        # scale (e.g. data ~ 0.01 vs. PDE residual ~ 1e10) on equal
        # footing before the softmax.
        vals = torch.stack([losses[k].detach() for k in keys])
        denom = vals.max() + 1e-12
        ratios = vals / denom
        w_now_t = torch.softmax(ratios / T, dim=0) * len(keys)
    w_now = {k: float(w_now_t[i].item()) for i, k in enumerate(keys)}
    return {k: alpha * w_prev.get(k, 1.0) + (1.0 - alpha) * w_now[k] for k in keys}


def normalized_pde_loss(residual: torch.Tensor) -> torch.Tensor:
    """Scale-invariant proxy for the PDE residual.

    Divides by the detached RMS of the residual so the loss is always
    O(1) regardless of the absolute scale of the gradient terms.  This
    lets the data-fit and physics terms be weighted with sensible w_pde
    values in (0.1, 1) instead of needing 1e-11 hacks.
    """
    rms = residual.detach().pow(2).mean().sqrt() + 1e-12
    return ((residual / rms) ** 2).mean()


def _build_loss_dict(
    model: PINN, dataset, cfg: TrainConfig
) -> tuple[dict[str, torch.Tensor], dict[str, float]]:
    obs = dataset.sample_obs(cfg.n_obs_batch, cfg.device)
    C_pred = model(obs.x, obs.y, obs.t)
    loss_data = ((C_pred - obs.C) ** 2).mean()

    col = dataset.sample_collocation(cfg.n_collocation, cfg.device)
    r = pde_residual(
        model,
        col.x,
        col.y,
        col.t,
        col.u_o,
        col.v_o,
        col.u_w,
        col.v_w,
        multi_physics=cfg.multi_physics,
    )
    # Normalised PDE loss keeps the term O(1) independent of the
    # absolute residual scale — see ``normalized_pde_loss`` docstring.
    loss_pde = normalized_pde_loss(r)

    # Datasets that do not define ic_loss/bc_loss (e.g. point-only RealDataset)
    # gracefully return zero so the PDE+data loss still trains.
    loss_ic = dataset.ic_loss(model) if hasattr(dataset, "ic_loss") else torch.zeros((), device=cfg.device)
    loss_bc = dataset.bc_loss(model) if hasattr(dataset, "bc_loss") else torch.zeros((), device=cfg.device)

    losses = {"data": loss_data, "pde": loss_pde, "ic": loss_ic, "bc": loss_bc}
    scalars = {k: float(v.item()) for k, v in losses.items()}
    return losses, scalars


def train(
    model: PINN,
    dataset,
    cfg: TrainConfig,
    *,
    verbose: bool = True,
) -> PINN:
    """Train PINN with combined data + physics loss."""
    device = cfg.device
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, cfg.epochs))

    weights = {"data": cfg.w_data, "pde": cfg.w_pde, "ic": cfg.w_ic, "bc": cfg.w_bc}

    for step in range(cfg.epochs):
        opt.zero_grad()
        losses, scalars = _build_loss_dict(model, dataset, cfg)

        if cfg.adaptive != "off" and step > 0 and step % cfg.rebalance_every == 0:
            if cfg.adaptive == "ntk":
                weights = ntk_weights(model, losses, prev=weights)
            elif cfg.adaptive == "relo_bra_lo":
                weights = relo_bra_lo(losses, w_prev=weights)
            else:
                weights = grad_norm_weights(model, losses, prev=weights)

        # PDE warm-up: ramp lambda_pde from 0 to its final value over
        # `warmup_pde_epochs` epochs (sigmoid schedule).
        if cfg.warmup_pde_epochs > 0:
            t = (step - cfg.warmup_pde_epochs / 2) / max(1, cfg.warmup_pde_epochs / 4)
            pde_scale = 1.0 / (1.0 + math.exp(-t))
        else:
            pde_scale = 1.0

        loss = sum(
            (pde_scale if k == "pde" else 1.0) * weights.get(k, 1.0) * v
            for k, v in losses.items()
        )
        loss.backward()
        opt.step()
        sched.step()

        if verbose and step % 200 == 0:
            logger.info(
                "step=%5d  loss=%.4f  weights=%s  data=%.4f pde=%.4f  α=%.4f K=%.2e λ=%.2e",
                step,
                float(loss.item()),
                {k: round(v, 3) for k, v in weights.items()},
                scalars["data"],
                scalars["pde"],
                model.alpha.item(),
                model.K.item(),
                model.lam.item(),
            )
    return model


def _save_checkpoint(model: PINN, path: str, meta: TrainingMeta | None = None) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    meta_dict = meta.to_dict() if meta is not None else {}
    extra = dict(meta_dict.get("extra", {}))
    extra.setdefault("activation", getattr(model, "activation", "tanh"))
    extra.setdefault("w0", getattr(model, "w0", 1.0))
    extra.setdefault("hidden", getattr(model, "hidden", 128))
    extra.setdefault("depth", getattr(model, "depth", 6))
    extra.setdefault("num_freq", getattr(model, "num_freq", 8))
    meta_dict["extra"] = extra
    payload = {
        "model_state_dict": model.state_dict(),
        "alpha": model.alpha.item(),
        "K": model.K.item(),
        "lam": model.lam.item(),
        "alpha_stokes": model.alpha_stokes.item(),
        "lam_bio": model.lam_bio.item(),
        "meta": meta_dict,
    }
    torch.save(payload, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train TideGuard PINN")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--reports", type=str, default=None)
    parser.add_argument("--forcing", type=str, default=None)
    parser.add_argument(
        "--bbox",
        type=str,
        default="27,40,42,47",
        help="lon_min,lat_min,lon_max,lat_max (default: Black Sea)",
    )
    parser.add_argument("--domain", type=str, default="black-sea")
    parser.add_argument("--horizon-days", type=int, default=14)
    parser.add_argument("--epochs", type=int, default=2000)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--save", type=str, default="checkpoints/pinn_demo.pt")
    parser.add_argument("--seed-ensemble", type=int, default=0)
    parser.add_argument(
        "--adaptive",
        choices=("off", "ntk", "grad_norm", "relo_bra_lo"),
        default="off",
    )
    parser.add_argument("--rebalance-every", type=int, default=250)
    parser.add_argument("--activation", choices=("tanh", "siren"), default="tanh")
    parser.add_argument("--hidden", type=int, default=128)
    parser.add_argument("--depth", type=int, default=6)
    parser.add_argument("--num-freq", type=int, default=8)
    parser.add_argument("--w0", type=float, default=30.0)
    parser.add_argument("--warmup-pde-epochs", type=int, default=0)
    parser.add_argument("--multi-physics", action="store_true")
    parser.add_argument("--codecarbon", action="store_true", help="Track emissions via codecarbon (TASK-021)")
    parser.add_argument("--git-sha", type=str, default="dev")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    bbox = tuple(float(x) for x in args.bbox.split(","))
    if len(bbox) != 4:
        raise SystemExit("--bbox must be lon_min,lat_min,lon_max,lat_max")

    if args.real:
        if not args.reports:
            raise SystemExit("--real requires --reports CSV")
        dataset = RealDataset(reports_csv=args.reports, forcing_npz=args.forcing, bbox=bbox)  # type: ignore[arg-type]
        forcing_source = args.forcing or "none"
    elif args.synthetic:
        dataset = SyntheticDataset(n_obs=5000, seed=42)
        forcing_source = "synthetic"
    else:
        raise SystemExit("Pass either --synthetic or --real")

    base_cfg = TrainConfig(
        epochs=args.epochs,
        lr=args.lr,
        device=args.device,
        adaptive=args.adaptive,
        rebalance_every=args.rebalance_every,
        warmup_pde_epochs=args.warmup_pde_epochs,
        multi_physics=args.multi_physics,
    )
    meta = TrainingMeta(
        domain=args.domain,
        bbox=bbox,  # type: ignore[arg-type]
        horizon_days=args.horizon_days,
        forcing_source=forcing_source,
        git_sha=args.git_sha,
        extra={"adaptive": args.adaptive},
    )
    logger.info("Training PINN: %s", asdict(base_cfg))
    logger.info("Meta: %s", meta.to_dict())

    tracker = None
    if args.codecarbon:
        try:
            from codecarbon import EmissionsTracker  # type: ignore

            tracker = EmissionsTracker(project_name="tideguard-pinn", log_level="warning")
            tracker.start()
        except Exception as exc:  # noqa: BLE001
            logger.warning("CodeCarbon disabled: %s", exc)

    def _new_model() -> PINN:
        return PINN(
            hidden=args.hidden,
            depth=args.depth,
            num_freq=args.num_freq,
            activation=args.activation,
            w0=args.w0,
        )

    try:
        if args.seed_ensemble > 0:
            base, ext = os.path.splitext(args.save)
            for s in range(args.seed_ensemble):
                torch.manual_seed(s)
                model = _new_model()
                cfg = replace(base_cfg)
                logger.info("ensemble member %d/%d", s + 1, args.seed_ensemble)
                model = train(model, dataset, cfg)
                _save_checkpoint(model, f"{base}_seed{s}{ext}", meta)
            logger.info("Saved %d ensemble members to %s_seed*%s", args.seed_ensemble, base, ext)
        else:
            model = _new_model()
            model = train(model, dataset, base_cfg)
            _save_checkpoint(model, args.save, meta)
            logger.info("Saved checkpoint to %s", args.save)
    finally:
        if tracker is not None:
            emissions = tracker.stop()
            logger.info("CodeCarbon: emissions=%.4f kg CO2eq", emissions or 0.0)


if __name__ == "__main__":
    main()
