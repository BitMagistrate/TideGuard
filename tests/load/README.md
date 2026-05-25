# Load tests

Locust scenarios used to populate `docs/loadtest_report.md`. Not run on
PR — invoked manually before each minor release and pinned in the
CHANGELOG.

```bash
locust -f tests/load/locustfile.py --headless --users 500 \
    --spawn-rate 25 --run-time 10m --host https://api.tideguard.app
```

When iterating locally, point at the dev API:

```bash
make api-dev  # starts FastAPI on :8000
locust -f tests/load/locustfile.py --headless --users 100 \
    --spawn-rate 10 --run-time 60s --host http://localhost:8000
```

The CSV summary produced by Locust (`tests/load/locust_stats.csv`,
`...failures.csv`, `...history.csv`) is committed to the
`docs/loadtest_history/` directory once per release for traceability.
