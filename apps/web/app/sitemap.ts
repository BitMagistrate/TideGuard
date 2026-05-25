import type { MetadataRoute } from "next";

const SITE = process.env.NEXT_PUBLIC_SITE_URL || "https://tideguard.app";

const STATIC_PATHS = [
  "/",
  "/about",
  "/map",
  "/method",
  "/research",
  "/pricing",
  "/learn",
  "/impact",
  "/sustainability",
  "/roadmap",
  "/partners",
  "/press",
  "/faq",
  "/jury-pilot",
  "/adopt-a-beach",
  "/b2g",
  "/b2g/anapa",
  "/b2g/sochi",
  "/developers",
  "/leaderboard",
  "/esg",
  "/privacy",
  "/terms",
  "/cookies",
  "/ru",
  "/ru/about",
  "/ru/method",
  "/ru/research",
  "/ru/pricing",
  "/ru/faq",
  "/ru/partners",
  "/ru/press",
  "/ru/roadmap",
  "/ru/learn",
  "/ru/b2g/anapa",
  "/ru/b2g/sochi",
  "/zh",
  "/zh/about",
  "/zh/method",
  "/zh/research",
  "/zh/pricing",
  "/zh/faq",
  "/zh/partners",
  "/zh/press",
  "/zh/roadmap",
  "/zh/learn",
  "/zh/b2g/anapa",
  "/zh/b2g/sochi",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  return STATIC_PATHS.map((path) => ({
    url: `${SITE}${path}`,
    lastModified,
    changeFrequency: path === "/" ? "weekly" : "monthly",
    priority: path === "/" ? 1 : 0.7,
  }));
}
