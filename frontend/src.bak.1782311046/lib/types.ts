/** API 类型定义 */

export interface Platform {
  id: number;
  code: string;
  name: string;
  icon_url: string;
  category: string;
  is_active: boolean;
}

export interface TrendingTopic {
  id: number;
  platform: { code: string; name: string; icon_url: string };
  rank: number;
  title: string;
  hot_value: string;
  hot_value_norm: number;
  topic_url: string;
  category: string;
  snapshot_at: string;
}

export interface HotArticle {
  id: number;
  platform: { code: string; name: string; icon_url: string };
  title: string;
  summary: string;
  images: { url: string; width?: number; height?: number }[];
  video_url: string;
  author_name: string;
  author_avatar: string;
  source_url: string;
  read_count: number;
  like_count: number;
  comment_count: number;
  share_count: number;
  publish_at: string;
  snapshot_at: string;
  content_text?: string;
}

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export interface TrendingListData {
  items: TrendingTopic[];
}

export interface ArticleListData {
  items: HotArticle[];
}

/** Summary API - each platform with top-3 preview */
export interface PlatformSummaryItem {
  code: string;
  name: string;
  icon_url: string;
  category: string;
  top3: TrendingTopic[];
  snapshot_at: string | null;
}
