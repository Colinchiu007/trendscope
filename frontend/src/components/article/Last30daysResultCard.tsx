"use client";

import { Card, Tag, Typography, Space, Tooltip } from "antd";
import {
  GlobalOutlined,
  UserOutlined,
  FireOutlined,
  MessageOutlined,
  StarOutlined,
} from "@ant-design/icons";

const { Text, Paragraph, Link } = Typography;

const SOURCE_COLORS: Record<string, string> = {
  reddit: "#FF4500",
  hackernews: "#FF6600",
  github: "#24292F",
  polymarket: "#0E76FD",
};

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  reddit: <FireOutlined />,
  hackernews: <StarOutlined />,
  github: <GlobalOutlined />,
};

interface Last30daysResult {
  item_id: string;
  source: string;
  source_label: string;
  title: string;
  body: string;
  url: string;
  author: string;
  published_at: string | null;
  engagement: Record<string, number>;
  engagement_score: number;
  container: string;
  thumbnail: string | null;
}

interface Props {
  item: Last30daysResult;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "未知";
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffDays === 0) return "今天";
    if (diffDays === 1) return "昨天";
    if (diffDays < 7) return `${diffDays}天前`;
    return d.toLocaleDateString("zh-CN");
  } catch {
    return dateStr;
  }
}

function formatEngagement(engagement: Record<string, number>): string {
  const entries = Object.entries(engagement).filter(([, v]) => v > 0);
  if (entries.length === 0) return "";
  return entries
    .slice(0, 2)
    .map(([k, v]) => {
      const label = k === "upvotes" ? "👍" : k === "comments" ? "💬" : k === "points" ? "⬆" : k === "stars" ? "⭐" : k === "volume" ? "💰" : k;
      return `${label} ${v >= 1000 ? (v / 1000).toFixed(1) + "k" : v}`;
    })
    .join(" · ");
}

export function Last30daysResultCard({ item }: Props) {
  const color = SOURCE_COLORS[item.source] || "#666";
  const icon = SOURCE_ICONS[item.source] || <GlobalOutlined />;

  return (
    <Card
      size="small"
      style={{ marginBottom: 12, borderRadius: 10, borderLeft: `3px solid ${color}` }}
      bodyStyle={{ padding: "12px 16px" }}
    >
      <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
        {/* 缩略图 */}
        {item.thumbnail && (
          <div style={{ width: 80, height: 60, flexShrink: 0, borderRadius: 6, overflow: "hidden", background: "#f0f0f0" }}>
            <img
              src={item.thumbnail}
              alt=""
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
              onError={(e) => { (e.target as HTMLImageElement).style.display = "none" }}
            />
          </div>
        )}

        <div style={{ flex: 1, minWidth: 0 }}>
          {/* 标题 - 外部链接 */}
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ fontSize: 15, fontWeight: 500, marginBottom: 4, lineHeight: 1.5 }}
          >
            <Link
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#1a1a1a" }}
            >
              {item.title}
            </Link>
          </Paragraph>

          {/* 摘要 */}
          {item.body && (
            <Paragraph
              type="secondary"
              ellipsis={{ rows: 2 }}
              style={{ fontSize: 13, marginBottom: 8 }}
            >
              {item.body}
            </Paragraph>
          )}

          {/* 元信息 */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 4 }}>
            <Space size={6} wrap>
              <Tag color={color} style={{ margin: 0, fontSize: 11 }}>
                {icon} {item.source_label}
              </Tag>
              {item.author && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <UserOutlined style={{ marginRight: 2 }} />
                  {item.author}
                </Text>
              )}
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatDate(item.published_at)}
              </Text>
              {item.container && (
                <Text type="secondary" style={{ fontSize: 11 }}>
                  in {item.container}
                </Text>
              )}
            </Space>

            <Space size={8}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatEngagement(item.engagement)}
              </Text>
              <Tooltip title="互动评分（log10 归一化）">
                <Tag color="gold" style={{ margin: 0, fontSize: 11 }}>
                  {item.engagement_score.toFixed(2)}
                </Tag>
              </Tooltip>
            </Space>
          </div>
        </div>
      </div>
    </Card>
  );
}
