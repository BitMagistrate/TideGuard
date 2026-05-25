/**
 * Helpers for the billing/checkout/widgets layer.  Kept tiny and dependency-free
 * so they can be tested under vitest without spinning up Next.js or jsdom.
 */

export type Tier =
  | "free" | "pro" | "business" | "enterprise"
  | "b2g_basic" | "b2g_pro" | "b2g_enterprise"
  | "esg_insurance" | "esg_reporting"
  | "adopt_individual" | "adopt_school" | "adopt_business" | "adopt_municipal";

const PRICE_MAP_USD: Record<Tier, { monthly: number; yearly: number }> = {
  free: { monthly: 0, yearly: 0 },
  pro: { monthly: 49, yearly: 490 },
  business: { monthly: 299, yearly: 2990 },
  enterprise: { monthly: 0, yearly: 0 },
  b2g_basic: { monthly: 1200, yearly: 12000 },
  b2g_pro: { monthly: 3500, yearly: 35000 },
  b2g_enterprise: { monthly: 8000, yearly: 80000 },
  esg_insurance: { monthly: 2500, yearly: 25000 },
  esg_reporting: { monthly: 1500, yearly: 15000 },
  adopt_individual: { monthly: 10, yearly: 100 },
  adopt_school: { monthly: 25, yearly: 250 },
  adopt_business: { monthly: 200, yearly: 2000 },
  adopt_municipal: { monthly: 800, yearly: 8000 },
};

export function formatPrice(tier: Tier, period: "monthly" | "yearly" = "monthly"): string {
  const p = PRICE_MAP_USD[tier];
  if (!p) return "—";
  if (tier === "enterprise") return "Custom";
  return `$${p[period].toLocaleString("en-US")}`;
}

export function annualSavings(tier: Tier): number {
  const p = PRICE_MAP_USD[tier];
  if (!p || p.monthly === 0) return 0;
  return Math.max(0, p.monthly * 12 - p.yearly);
}

export function buildWidgetUrl(
  apiBase: string,
  params: { lat: number; lng: number; horizon?: number; theme?: "light" | "dark" }
): string {
  const u = new URL(apiBase.replace(/\/$/, "") + "/widgets/beach_status");
  u.searchParams.set("lat", String(params.lat));
  u.searchParams.set("lng", String(params.lng));
  if (params.horizon !== undefined) u.searchParams.set("horizon", String(Math.max(1, Math.min(14, params.horizon))));
  if (params.theme) u.searchParams.set("theme", params.theme);
  return u.toString();
}

export function buildEmbedSnippet(widgetUrl: string, opts: { width?: number; height?: number } = {}): string {
  const w = opts.width ?? 320;
  const h = opts.height ?? 180;
  return `<iframe src="${widgetUrl}" width="${w}" height="${h}" style="border:0" loading="lazy"></iframe>`;
}

export function obfuscateApiKey(key: string): string {
  if (!key) return "";
  const head = key.slice(0, 8);
  const tail = key.slice(-4);
  return `${head}…${tail}`;
}
