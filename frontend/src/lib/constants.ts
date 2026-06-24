// API 基础地址
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// 平台列表与颜色/图标映射
export const PLATFORMS = [
  { code: "weibo", name: "微博", color: "#E6162D" },
  { code: "baidu", name: "百度", color: "#2932E1" },
  { code: "zhihu", name: "知乎", color: "#0066FF" },
  { code: "bilibili", name: "B站", color: "#FB7299" },
  { code: "toutiao", name: "今日头条", color: "#E13D3D" },
  { code: "douyin", name: "抖音", color: "#000000" },
  { code: "xiaohongshu", name: "小红书", color: "#FE2C55" },
  { code: "weixin_article", name: "公众号", color: "#07C160" },
  { code: "shipinhao", name: "视频号", color: "#07C160" },
  { code: "youtube", name: "YouTube", color: "#FF0000" },
  { code: "tiktok", name: "TikTok", color: "#000000" },
  { code: "x_twitter", name: "X", color: "#1DA1F2" },
] as const;

// Platform code -> local logo path mapping
export const PLATFORM_LOGOS: Record<string, string> = {
  weibo: "/logos/weibo.png",
  baidu: "/logos/baidu.png",
  zhihu: "/logos/zhihu.png",
  bilibili: "/logos/bilibili.png",
  toutiao: "/logos/toutiao.png",
  douyin: "/logos/douyin.png",
  xiaohongshu: "/logos/xiaohongshu.png",
  weixin_article: "/logos/weixin_article.png",
  shipinhao: "/logos/shipinhao.png",
  youtube: "/logos/youtube.png",
  tiktok: "/logos/tiktok.png",
  x_twitter: "/logos/x_twitter.png",
};

export const PLATFORM_COLORS: Record<string, string> = {};
PLATFORMS.forEach((p) => { PLATFORM_COLORS[p.code] = p.color; });

// 分页默认值
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;
