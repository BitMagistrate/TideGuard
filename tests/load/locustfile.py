"""Locust load-test scenario for the TideGuard API.

Run::

    locust -f tests/load/locustfile.py --headless --users 500 \
        --spawn-rate 25 --run-time 10m --host https://api.tideguard.app

The scenario is intentionally **read-heavy** (90% read / 10% write) to
mirror the realistic citizen-science traffic pattern (one report per
ten map views). Targets and result format are documented in
``docs/loadtest_report.md``.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task


class TideGuardUser(HttpUser):
    """A simulated user of the TideGuard public API."""

    # Wait 0.5 – 2 s between actions to mimic human pacing.
    wait_time = between(0.5, 2.0)

    bbox = "27,40,42,47"  # Black Sea default

    @task(45)
    def forecast(self) -> None:
        horizon = random.randint(1, 14)
        self.client.get(
            f"/forecast?bbox={self.bbox}&horizon={horizon}", name="/forecast"
        )

    @task(35)
    def exceedance(self) -> None:
        horizon = random.randint(1, 14)
        quantile = random.choice([0.8, 0.85, 0.9, 0.95])
        self.client.get(
            f"/forecast/exceedance?bbox={self.bbox}&horizon={horizon}&quantile={quantile}",
            name="/forecast/exceedance",
        )

    @task(10)
    def tile(self) -> None:
        z = random.choice([4, 5, 6, 7])
        x = random.randint(20, 30)
        y = random.randint(10, 20)
        day = random.randint(0, 13)
        self.client.get(
            f"/tiles/{z}/{x}/{y}.png?day={day}",
            name="/tiles/[z]/[x]/[y]",
        )

    @task(10)
    def leaderboard(self) -> None:
        self.client.get("/leaderboard", name="/leaderboard")
