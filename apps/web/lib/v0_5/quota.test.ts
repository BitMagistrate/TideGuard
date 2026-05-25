import { describe, expect, it } from "vitest";
import { pctUsed, parseRateLimitHeaders, quotaStatus } from "./quota";

describe("quota helpers", () => {
  it("computes percentages", () => {
    expect(pctUsed(0, 1000)).toBe(0);
    expect(pctUsed(500, 1000)).toBe(50);
    expect(pctUsed(2000, 1000)).toBe(100);
    expect(pctUsed(0, 0)).toBe(0);
  });

  it("classifies status thresholds", () => {
    expect(quotaStatus(0, 1000)).toBe("ok");
    expect(quotaStatus(800, 1000)).toBe("warning");
    expect(quotaStatus(950, 1000)).toBe("critical");
    expect(quotaStatus(1100, 1000)).toBe("blocked");
  });

  it("parses rate-limit headers including unlimited", () => {
    const h = new Headers({
      "X-Rate-Limit-Tier": "pro",
      "X-Rate-Limit-Limit": "100000",
      "X-Rate-Limit-Remaining": "99500",
      "X-Rate-Limit-Reset": "1735689600000",
    });
    const r = parseRateLimitHeaders(h);
    expect(r.tier).toBe("pro");
    expect(r.limit).toBe(100000);
    expect(r.remaining).toBe(99500);

    const h2 = new Headers({
      "X-Rate-Limit-Tier": "enterprise",
      "X-Rate-Limit-Limit": "unlimited",
      "X-Rate-Limit-Remaining": "unlimited",
    });
    const r2 = parseRateLimitHeaders(h2);
    expect(r2.limit).toBe("unlimited");
    expect(r2.remaining).toBe("unlimited");
  });
});
