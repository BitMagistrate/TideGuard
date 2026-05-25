# TideGuard Ops Runbook

> Last-resort, on-call SRE doc. Anyone seeing one of these alert pages
> should follow the matching `Action` row.

## Dashboards

- **Grafana.** `https://grafana.tideguard.app/d/tg-overview` — derived
  from `infra/observability/grafana_dashboard.json`.
- **Prometheus rules.** `infra/observability/prometheus_rules.yaml`.

## Alert → Action matrix

| Alert | Severity | Action |
|-------|----------|--------|
| `TideGuard API > 5xx > 5%` for 5 min | critical | `flyctl logs -a tideguard-api`; rollback via `flyctl deploy --release <previous>` |
| Latency p95 > 1.5 s for 10 min | warning | scale horizontally `flyctl scale count 4 -a tideguard-api` |
| Postgres connections > 90 % | warning | clear runaway queries `flyctl postgres connect -a tideguard-pg`, `\x` `select pg_terminate_backend(pid) ...` |
| Redis OOM | critical | flush cache `redis-cli flushdb`; restart workers `flyctl machine restart` |
| Sentry error spike (>50 events/5 min from one signature) | warning | open ticket; reproduce locally; ship hotfix as a new release |
| Lighthouse Performance < 80 on `/map` | warning | open issue; check map-tiles vendor; cap bundle size |
| Cloudflare R2 4xx rate > 1 % | warning | check IAM scope; ensure signed URLs |
| K-6 load test failure | warning | re-run `ops/load/run.sh`; investigate hot path |

## Incident response (run-of-deck)

1. Acknowledge alert in PagerDuty (or @duty Telegram channel).
2. Open the Grafana dashboard.
3. Open `flyctl logs -a tideguard-api -i 100`.
4. Decide between rollback (`flyctl deploy --release <previous>`) or
   horizontal scale-up.
5. Write a 3-line incident note in `docs/announcements/incidents.md`.
6. Post a status update on `https://status.tideguard.app`.

## Maintenance windows

- **Tuesday 04:00 UTC.** Database VACUUM + migrations. Brief 502 OK.
- **First Saturday of the month.** Re-train PINN on latest data
  (`scripts/build_black_sea_observations.py && uv run python -m
  tideguard_api.workers retrain`). Models cycle via blue-green.
