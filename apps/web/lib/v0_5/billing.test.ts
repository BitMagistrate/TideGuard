import { describe, expect, it } from "vitest";
import { annualSavings, buildEmbedSnippet, buildWidgetUrl, formatPrice, obfuscateApiKey } from "./billing";

describe("billing helpers", () => {
  it("formats prices in USD", () => {
    expect(formatPrice("free")).toBe("$0");
    expect(formatPrice("pro")).toBe("$49");
    expect(formatPrice("business")).toBe("$299");
    expect(formatPrice("enterprise")).toBe("Custom");
  });

  it("computes annual savings", () => {
    expect(annualSavings("pro")).toBeGreaterThan(0);
    expect(annualSavings("free")).toBe(0);
  });

  it("builds widget URLs with clamped horizon", () => {
    const url = buildWidgetUrl("https://api.tideguard.app", { lat: 43.5, lng: 39.7, horizon: 99 });
    expect(url).toContain("horizon=14");
    expect(url).toContain("lat=43.5");
  });

  it("trims trailing slashes from the API base", () => {
    const url = buildWidgetUrl("https://api.tideguard.app/", { lat: 1, lng: 2 });
    expect(url.startsWith("https://api.tideguard.app/widgets/beach_status")).toBe(true);
  });

  it("builds an iframe embed snippet", () => {
    const snippet = buildEmbedSnippet("https://x/y", { width: 480, height: 240 });
    expect(snippet).toContain('width="480"');
    expect(snippet).toContain("loading=\"lazy\"");
  });

  it("obfuscates API keys", () => {
    const out = obfuscateApiKey("tg_live_AAAAAAAAA1234");
    expect(out.startsWith("tg_live_")).toBe(true);
    expect(out.endsWith("1234")).toBe(true);
    expect(out).toContain("…");
  });
});
