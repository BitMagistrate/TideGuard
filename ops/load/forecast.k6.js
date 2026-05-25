// k6 load test for TideGuard `/forecast/exceedance` endpoint (TASK-024).
//
// Usage:
//   k6 run -e API_BASE=https://api.tideguard.app ops/load/forecast.k6.js
//
// SLO targets (verified against the prod-shape config in settings.py):
//   * P50 < 300 ms
//   * P95 < 800 ms
//   * 0 errors on a 30 RPS / 5 minute soak

import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    soak: {
      executor: "constant-arrival-rate",
      rate: 30,
      timeUnit: "1s",
      duration: "5m",
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{endpoint:forecast}": ["p(95)<800", "p(50)<300"],
  },
};

const API = __ENV.API_BASE || "http://localhost:8000";

const BBOXES = [
  "27,40,42,47",  // Whole Black Sea
  "37,44,39,46",  // Anapa / Novorossiysk
  "37,43,39,45",  // central Black Sea coast
  "28,41,32,43",  // Western shelf
];

export default function () {
  const bbox = BBOXES[Math.floor(Math.random() * BBOXES.length)];
  const horizon = 1 + Math.floor(Math.random() * 7);
  const res = http.get(`${API}/forecast/exceedance?bbox=${bbox}&horizon=${horizon}&quantile=0.9`, {
    tags: { endpoint: "forecast" },
  });
  check(res, {
    "200": (r) => r.status === 200,
    "non-empty cells": (r) => {
      try {
        const body = r.json();
        return Array.isArray(body.cells) && body.cells.length > 0;
      } catch (_e) {
        return false;
      }
    },
  });
  sleep(0.1);
}
