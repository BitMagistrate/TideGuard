import type { Metadata, Viewport } from "next";
import "./globals.css";
import LangSwitcher from "../components/Lang/LangSwitcher";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL || "https://tideguard.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "TideGuard AI — Open-source forecast of marine plastic",
    template: "%s · TideGuard AI",
  },
  description:
    "Physics-Informed Neural Network forecasting floating plastic on the Black Sea coast 72 hours before it beaches. MIT-licensed, OSF pre-registered, built in 3 months by a 17-year-old 10th-grader from Krasnoyarsk with an AI coding co-pilot.",
  keywords: [
    "marine plastic",
    "physics-informed neural network",
    "PINN",
    "Black Sea",
    "ocean forecast",
    "open science",
    "Adopt-a-Beach",
    "Anapa",
    "Sochi",
    "open source",
  ],
  authors: [{ name: "Vladimir Ermolenko" }],
  creator: "Vladimir Ermolenko",
  publisher: "TideGuard AI",
  category: "science",
  alternates: {
    canonical: "/",
    languages: {
      "en-US": "/",
      "ru-RU": "/ru",
      "zh-TW": "/zh",
    },
  },
  openGraph: {
    title: "TideGuard AI — AI that predicts plastic before it pollutes",
    description:
      "Open-source PINN forecast of floating marine debris on the Black Sea, with 14-day horizon, uncertainty maps and free EE lessons in EN / RU / ZH.",
    url: SITE_URL,
    siteName: "TideGuard AI",
    type: "website",
    locale: "en_US",
    images: [
      { url: "/og-image.png", width: 1200, height: 630, alt: "TideGuard AI" },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "TideGuard AI",
    description: "AI that predicts plastic before it pollutes.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
  },
};

export const viewport: Viewport = {
  themeColor: "#0b5550",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <LangSwitcher />
        {children}
      </body>
    </html>
  );
}
