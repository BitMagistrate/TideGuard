"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Locale = "en" | "ru" | "zh";

// Manifest of pages that exist in each non-default locale. If a user
// switches language on a page that does not exist in the target locale,
// we fall back to the locale's home page (e.g. /ru) instead of producing
// a 404. Keep these in sync with the actual app/(ru|zh)/* directory tree.
const RU_PAGES = new Set<string>([
  "/",
  "/about",
  "/method",
  "/research",
  "/pricing",
  "/faq",
  "/partners",
  "/press",
  "/roadmap",
  "/learn",
  "/b2g/anapa",
  "/b2g/sochi",
]);

const ZH_PAGES = new Set<string>([
  "/",
  "/about",
  "/method",
  "/research",
  "/pricing",
  "/faq",
  "/partners",
  "/press",
  "/roadmap",
  "/learn",
  "/b2g/anapa",
  "/b2g/sochi",
]);

function detectLocale(pathname: string): Locale {
  if (pathname === "/ru" || pathname.startsWith("/ru/")) return "ru";
  if (pathname === "/zh" || pathname.startsWith("/zh/")) return "zh";
  return "en";
}

function stripLocalePrefix(pathname: string): string {
  if (pathname === "/ru" || pathname === "/zh") return "/";
  if (pathname.startsWith("/ru/")) return pathname.slice(3);
  if (pathname.startsWith("/zh/")) return pathname.slice(3);
  return pathname;
}

function buildUrl(locale: Locale, basePath: string): string {
  const clean = basePath === "" ? "/" : basePath;
  if (locale === "en") return clean;
  const manifest = locale === "ru" ? RU_PAGES : ZH_PAGES;
  if (clean === "/") return `/${locale}`;
  if (manifest.has(clean)) return `/${locale}${clean}`;
  // Page not translated in target locale → fall back to locale home so we
  // never send the user to a 404 from the language switcher.
  return `/${locale}`;
}

export default function LangSwitcher() {
  const pathname = usePathname() || "/";
  const locale = detectLocale(pathname);
  const base = stripLocalePrefix(pathname);
  const enUrl = buildUrl("en", base);
  const ruUrl = buildUrl("ru", base);
  const zhUrl = buildUrl("zh", base);

  return (
    <nav
      aria-label="Language"
      className="bg-zinc-900 text-white text-xs"
    >
      <div className="max-w-6xl mx-auto px-6 py-2 flex justify-end gap-1">
        <Pill href={enUrl} active={locale === "en"} label="EN" />
        <Pill href={ruUrl} active={locale === "ru"} label="RU" />
        <Pill href={zhUrl} active={locale === "zh"} label="ZH" />
      </div>
    </nav>
  );
}

function Pill({
  href,
  active,
  label,
}: {
  href: string;
  active: boolean;
  label: string;
}) {
  const base = "px-2 py-1 rounded transition";
  const cls = active
    ? "bg-teal-700 text-white font-semibold"
    : "text-zinc-300 hover:text-white hover:bg-zinc-800";
  return (
    <Link href={href} className={`${base} ${cls}`} aria-current={active ? "page" : undefined}>
      {label}
    </Link>
  );
}
