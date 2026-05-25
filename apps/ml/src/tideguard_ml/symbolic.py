"""Symbolic-regression of PINN residuals (TASK-019).

The PINN residual after training should look like a low-order polynomial
in the physical state — bumps in the residual point at missing physics.
We approximate that polynomial with PySR (preferred) or, when PySR is
unavailable, with a 2nd-order linear regression on the residual.

The default fallback is intentionally tiny: it lets the audit harness run
in CI without pulling Julia, while keeping the real PySR path for offline
research runs.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SymbolicFit:
    expression: str
    coefficients: dict[str, float]
    r2: float
    backend: str


def _polynomial_features(X: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Construct 2nd-order polynomial features (bias + linear + cross + sq)."""
    n, d = X.shape
    names = ["1"]
    cols = [np.ones((n, 1))]
    for i in range(d):
        names.append(f"x{i}")
        cols.append(X[:, [i]])
    for i in range(d):
        for j in range(i, d):
            names.append(f"x{i}*x{j}")
            cols.append(X[:, [i]] * X[:, [j]])
    return np.hstack(cols), names


def fit_symbolic_residual(
    X: np.ndarray,
    y: np.ndarray,
    *,
    feature_names: Sequence[str] | None = None,
    use_pysr: bool = True,
    pysr_kwargs: dict | None = None,
) -> SymbolicFit:
    """Fit a symbolic expression to ``y = f(X)``.

    Parameters
    ----------
    X : (n_samples, n_features)
    y : (n_samples,)
    feature_names : optional list of names matching X columns.
    use_pysr : if True, try to call PySR; fall back to polynomial regression.
    """
    feature_names = list(feature_names) if feature_names else [f"x{i}" for i in range(X.shape[1])]

    if use_pysr:
        try:
            from pysr import PySRRegressor  # type: ignore

            model = PySRRegressor(
                niterations=20,
                binary_operators=["+", "-", "*"],
                unary_operators=["square", "sin"],
                model_selection="best",
                progress=False,
                **(pysr_kwargs or {}),
            )
            model.fit(X, y, variable_names=feature_names)
            best = model.get_best()
            r2 = float(model.score(X, y))
            return SymbolicFit(
                expression=str(best["equation"]),
                coefficients={"complexity": float(best["complexity"])},
                r2=r2,
                backend="pysr",
            )
        except ImportError:  # pragma: no cover
            logger.warning("PySR not available — falling back to polynomial regression")
        except Exception as exc:  # noqa: BLE001
            logger.warning("PySR failed (%s) — falling back to polynomial regression", exc)

    # Fallback: ordinary least squares on 2nd-order polynomial features.
    Phi, names = _polynomial_features(X)
    # Rename poly terms with user-provided variable names.
    if feature_names:
        named = []
        for n in names:
            if n == "1":
                named.append("1")
                continue
            parts = []
            for chunk in n.split("*"):
                idx = int(chunk[1:])
                parts.append(feature_names[idx])
            named.append("*".join(parts))
        names = named

    coef, *_ = np.linalg.lstsq(Phi, y, rcond=None)
    y_hat = Phi @ coef
    ss_res = float(((y - y_hat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum()) + 1e-12
    r2 = 1.0 - ss_res / ss_tot
    parts = [f"{c:+.4g}*{n}" if n != "1" else f"{c:+.4g}" for c, n in zip(coef, names) if abs(c) > 1e-6]
    expression = " ".join(parts) or "0"
    return SymbolicFit(
        expression=expression,
        coefficients={n: float(c) for n, c in zip(names, coef)},
        r2=r2,
        backend="poly2",
    )


__all__ = ["SymbolicFit", "fit_symbolic_residual"]
