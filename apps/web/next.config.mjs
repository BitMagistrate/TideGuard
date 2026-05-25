/** @type {import('next').NextConfig} */
// Security-hardened Next.js config (Sprint 1.9 of the engineering plan).
// CSP/HSTS/Permissions-Policy values are inlined here so that
// they ship with the static build and apply both on Vercel and
// any self-hosted Node runtime.
//
// We also explicitly disable the built-in Image Optimization API
// (`images.unoptimized = true`) so we are not exposed to the
// `next/image remotePatterns` DoS advisory (GHSA-9g9p-9gw9-jx7f).
// All `<Image>` consumers in this project render local public
// assets only, so unoptimised mode is functionally equivalent.

const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "").trim();
let apiOrigin = "";
try {
  if (apiUrl) apiOrigin = new URL(apiUrl).origin;
} catch {
  apiOrigin = "";
}
const isDev = process.env.NODE_ENV !== "production";
// When the configured API URL is itself localhost (e.g. someone runs
// `pnpm build && pnpm start` against a local backend for a recording demo),
// CSP must also include localhost in production mode — otherwise the
// browser refuses every cross-origin fetch. We also fall through to the
// localhost case when ``NEXT_PUBLIC_API_URL`` is unset (the runtime page
// code then falls back to ``http://localhost:8000``).
const allowLocalhostApi =
  !apiUrl ||
  apiOrigin.startsWith("http://localhost") ||
  apiOrigin.startsWith("http://127.0.0.1");
const devConnect =
  isDev || allowLocalhostApi
    ? ["http://localhost:8000", "http://127.0.0.1:8000"]
    : [];

const connectSrc = [
  "'self'",
  "https://api.tideguard.app",
  "https://*.maptiler.com",
  "https://api.maptiler.com",
  "https://demotiles.maplibre.org",
  "https://tile.openstreetmap.org",
  "https://*.tile.openstreetmap.org",
  "https://server.arcgisonline.com",
  "https://services.arcgisonline.com",
  "https://*.fly.dev",
  "https://*.vercel.app",
  ...(apiOrigin ? [apiOrigin] : []),
  ...devConnect,
].join(" ");

const imgSrc = [
  "'self'",
  "data:",
  "blob:",
  "https:",
  ...(isDev || allowLocalhostApi
    ? ["http://localhost:8000", "http://127.0.0.1:8000"]
    : []),
].join(" ");

const securityHeaders = [
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(self), geolocation=(self), microphone=()",
  },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      `img-src ${imgSrc}`,
      "style-src 'self' 'unsafe-inline'",
      // 'unsafe-eval' is required by MapLibre GL for shader compilation
      // and by Next.js dev-mode hot reload.
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      `connect-src ${connectSrc}`,
      "worker-src 'self' blob:",
      "font-src 'self' data:",
      "frame-ancestors 'none'",
      "form-action 'self'",
      "base-uri 'self'",
      "object-src 'none'",
    ].join("; "),
  },
];

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_MAPTILER_KEY: process.env.NEXT_PUBLIC_MAPTILER_KEY || "",
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
