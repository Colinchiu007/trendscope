import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "热榜 TrendScope - 多平台热榜聚合",
    template: "%s - 热榜 TrendScope",
  },
  description: "一站式查看微博、知乎、百度、B站、抖音、小红书等12个平台的热门话题和文章。实时追踪全网热点，支持跨平台搜索。",
  keywords: ["热榜", "热搜", "热门话题", "热门文章", "微博热搜", "知乎热榜", "百度热搜", "B站热门", "抖音热榜", "TrendScope"],
  authors: [{ name: "TrendScope" }],
  creator: "TrendScope",
  publisher: "TrendScope",
  formatDetection: {
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://trendscope.cn"),
  alternates: {
    canonical: "/",
    types: {
      "application/rss+xml": "/rss.xml",
    },
  },
  openGraph: {
    type: "website",
    locale: "zh_CN",
    siteName: "热榜 TrendScope",
    title: "热榜 TrendScope - 多平台热榜聚合引擎",
    description: "一站式查看12个主流平台的热门话题和文章",
    images: "/og-image.png",
  },
  twitter: {
    card: "summary_large_image",
    title: "热榜 TrendScope - 多平台热榜聚合",
    description: "一站式查看12个主流平台的热门话题和文章",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: "google-site-verification-code-placeholder",
    yandex: "yandex-verification-placeholder",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="baidu-site-verification" content="code-placeholder" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
