/** Helpers for displaying remaining-quota indicators. */

export function pctUsed(used: number, quota: number): number {
  if (!quota || quota <= 0) return 0;
  return Math.min(100, Math.max(0, Math.round((used / quota) * 100)));
}

export function quotaStatus(used: number, quota: number): "ok" | "warning" | "critical" | "blocked" {
  if (!quota || quota <= 0) return "ok";
  const pct = used / quota;
  if (pct >= 1) return "blocked";
  if (pct >= 0.95) return "critical";
  if (pct >= 0.8) return "warning";
  return "ok";
}

export function parseRateLimitHeaders(h: Headers): {
  tier: string;
  limit: number | "unlimited";
  remaining: number | "unlimited";
  resetMs: number | null;
} {
  const tier = h.get("X-Rate-Limit-Tier") ?? "free";
  const lim = h.get("X-Rate-Limit-Limit") ?? "0";
  const rem = h.get("X-Rate-Limit-Remaining") ?? "0";
  const reset = h.get("X-Rate-Limit-Reset");
  return {
    tier,
    limit: lim === "unlimited" ? "unlimited" : Number(lim) || 0,
    remaining: rem === "unlimited" ? "unlimited" : Number(rem) || 0,
    resetMs: reset ? Number(reset) : null,
  };
}
