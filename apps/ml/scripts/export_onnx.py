"""Export a trained PINN checkpoint to ONNX (P0-4).

The exported model takes a packed ``(N, 7)`` input tensor with the
columns ``(x, y, t, u_o, v_o, u_w, v_w)`` and outputs ``(N,)``
concentrations.  This matches the conditional forward of the PINN.

Usage::

    python -m tideguard_ml.scripts.export_onnx \
        --checkpoint checkpoints/pinn_black_sea_seed0.pt \
        --out exports/pinn.onnx
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from tideguard_ml.pinn import PINN, infer_arch_from_state_dict


class PackedPINN(torch.nn.Module):
    """Wrap the PINN so it takes a single (N, 7) tensor.

    This makes the ONNX graph easier to consume from mobile runtimes
    (single input, single output).
    """

    def __init__(self, model: PINN) -> None:
        super().__init__()
        self.model = model

    def forward(self, packed: torch.Tensor) -> torch.Tensor:
        x = packed[:, 0]
        y = packed[:, 1]
        t = packed[:, 2]
        u_o = packed[:, 3]
        v_o = packed[:, 4]
        u_w = packed[:, 5]
        v_w = packed[:, 6]
        return self.model(x, y, t, u_o, v_o, u_w, v_w)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--n-test", type=int, default=64)
    args = p.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    state = ckpt["model_state_dict"]
    meta_dict = ckpt.get("meta", {}) or {}
    extra = dict(meta_dict.get("extra", {}))
    arch = infer_arch_from_state_dict(state)
    activation = extra.get("activation", "tanh")
    w0 = float(extra.get("w0", 1.0))
    model = PINN(
        hidden=arch["hidden"],
        depth=arch["depth"],
        num_freq=arch["num_freq"],
        activation=activation,
        w0=w0,
    )
    model.load_state_dict(state, strict=False)
    model.eval()
    wrapped = PackedPINN(model).eval()

    dummy = torch.zeros((args.n_test, 7), dtype=torch.float32)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        wrapped,
        dummy,
        args.out,
        input_names=["xytuv"],
        output_names=["concentration"],
        opset_version=17,
        dynamic_axes={"xytuv": {0: "n"}, "concentration": {0: "n"}},
    )
    print(f"[onnx] wrote {args.out}")

    # Sanity check: run via onnxruntime if installed.
    try:
        import onnxruntime as ort

        sess = ort.InferenceSession(args.out, providers=["CPUExecutionProvider"])
        out = sess.run(["concentration"], {"xytuv": dummy.numpy()})[0]
        print(f"[onnx] sanity: output shape={out.shape}, range=[{out.min():.4f}, {out.max():.4f}]")
    except ImportError:
        print("[onnx] onnxruntime not installed; skipping sanity check")


if __name__ == "__main__":
    main()
