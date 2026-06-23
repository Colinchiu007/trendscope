// API 基础地址
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// 平台列表
export const PLATFORMS = [
  { code: "weibo", name: "微博", icon: "weibo", color: "#E6162D" },
  { code: "baidu", name: "百度", icon: "baidu", color: "#2932E1" },
  { code: "zhihu", name: "知乎", icon: "zhihu", color: "#0066FF" },
  { code: "bilibili", name: "B站", icon: "bilibili", color: "#FB7299" },
  { code: "toutiao", name: "今日头条", icon: "toutiao", color: "#E13D3D" },
  { code: "douyin", name: "抖音", icon: "douyin", color: "#000000" },
  { code: "xiaohongshu", name: "小红书", icon: "xiaohongshu", color: "#FE2C55" },
  { code: "weixin_article", name: "公众号", icon: "wechat", color: "#07C160" },
  { code: "shipinhao", name: "视频号", icon: "shipinhao", color: "#07C160" },
  { code: "youtube", name: "YouTube", icon: "youtube", color: "#FF0000" },
  { code: "tiktok", name: "TikTok", icon: "tiktok", color: "#000000" },
  { code: "x_twitter", name: "X", icon: "twitter", color: "#1DA1F2" },
] as const;

// 分页默认值
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;
