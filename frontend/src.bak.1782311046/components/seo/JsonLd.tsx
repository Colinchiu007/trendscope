/** JSON-LD 结构化数据组件 - 用于 SEO */
import Script from "next/script";

interface OrganizationJsonLdProps {
  name?: string;
  url?: string;
  description?: string;
}

export function OrganizationJsonLd({
  name = "TrendScope",
  url = "https://trendscope.cn",
  description = "多平台热榜聚合引擎，一站式查看12个主流平台的热门话题和文章。",
}: OrganizationJsonLdProps) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name,
    url,
    description,
    applicationCategory: "NewsApplication",
    offers: { "@type": "Offer", price: "0", priceCurrency: "CNY" },
    inLanguage: "zh-CN",
  };

  return (
    <Script
      id="organization-jsonld"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  );
}

interface TrendingListJsonLdProps {
  items: Array<{
    name: string;
    position: number;
    url?: string;
  }>;
  datePublished: string;
}

export function TrendingListJsonLd({ items, datePublished }: TrendingListJsonLdProps) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    itemListOrder: "https://schema.org/ItemListOrderDescending",
    numberOfItems: items.length,
    itemListElement: items.slice(0, 50).map((item, idx) => ({
      "@type": "ListItem",
      position: item.position || idx + 1,
      item: {
        "@type": "Article",
        name: item.name,
        url: item.url,
      },
    })),
    datePublished,
  };

  return (
    <Script
      id="trending-jsonld"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  );
}

interface BreadcrumbJsonLdProps {
  items: Array<{ name: string; url: string }>;
}

export function BreadcrumbJsonLd({ items }: BreadcrumbJsonLdProps) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, idx) => ({
      "@type": "ListItem",
      position: idx + 1,
      name: item.name,
      item: item.url,
    })),
  };

  return (
    <Script
      id="breadcrumb-jsonld"
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  );
}
