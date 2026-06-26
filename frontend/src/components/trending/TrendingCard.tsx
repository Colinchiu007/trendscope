"use client";

import { Card, Tag, Typography, Space, Tooltip } from "antd";
import {
  RiseOutlined,
  FallOutlined,
  LinkOutlined,
  FireOutlined,
} from "@ant-design/icons";
import type { TrendingTopic } from "@/lib/types";

const { Text, Paragraph } = Typography;

interface TrendingCardProps {
  item: TrendingTopic;
  rankChange?: "up" | "down" | "new" | "same";
}

const PLATFORM_COLORS: Record<string, string> = {
  weibo: "#E6162D",
  baidu: "#2932E1",
  zhihu: "#0066FF",
  bilibili: "#FB7299",
  douyin: "#000000",
  xiaohongshu: "#FE2C55",
  youtube: "#FF0000",
  tiktok: "#000000",
  x_twitter: "#1DA1F2",
};

export function TrendingCard({ item, rankChange }: TrendingCardProps) {
  const rankColor = item.rank <= 3 ? "#f5222d" : item.rank <= 10 ? "#fa8c16" : "#8c8c8c";
  const platformColor = PLATFORM_COLORS[item.platform.code] || "#666";

  return (
    <Card
      hoverable
      size="small"
      style={{ marginBottom: 8 }}
      onClick={() => item.topic_url && window.open(item.topic_url, "_blank")}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        {/* 排名 */}
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            background: rankColor,
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            fontSize: 16,
            flexShrink: 0,
          }}
        >
          {item.rank}
        </div>

        {/* 内容 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ marginBottom: 4, fontSize: 15, lineHeight: 1.5 }}
          >
            {item.title}
          </Paragraph>
          <Space size={8} wrap>
            <Tag
              color={platformColor}
              style={{ margin: 0, fontSize: 11 }}
            >
              {item.platform.name}
            </Tag>
            {item.hot_value && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                <FireOutlined style={{ color: "#fa8c16", marginRight: 2 }} />
                {item.hot_value}
              </Text>
            )}
            {rankChange === "up" && (
              <RiseOutlined style={{ color: "#f5222d", fontSize: 12 }} />
            )}
            {rankChange === "down" && (
              <FallOutlined style={{ color: "#52c41a", fontSize: 12 }} />
            )}
          </Space>
        </div>

        {/* 链接 */}
        {item.topic_url && (
          <Tooltip title="查看原文">
            <LinkOutlined
              style={{ color: "#bbb", fontSize: 14, cursor: "pointer", marginTop: 4 }}
              onClick={(e) => {
                e.stopPropagation();
                window.open(item.topic_url, "_blank");
              }}
            />
          </Tooltip>
        )}
      </div>
    </Card>
  );
}
