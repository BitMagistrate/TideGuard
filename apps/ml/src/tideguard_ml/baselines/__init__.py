"""Forecast baselines we benchmark the PINN against."""

from tideguard_ml.baselines.climatology import ClimatologyBaseline
from tideguard_ml.baselines.lagrangian import LagrangianBaseline
from tideguard_ml.baselines.persistence import PersistenceBaseline

__all__ = ["ClimatologyBaseline", "LagrangianBaseline", "PersistenceBaseline"]
