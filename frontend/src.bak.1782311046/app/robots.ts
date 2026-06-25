import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: "*", allow: "/" },
      { userAgent: "*", disallow: ["/api/", "/admin/", "/user/"] },
    ],
    sitemap: "https://trendscope.cn/sitemap.xml",
  };
}
