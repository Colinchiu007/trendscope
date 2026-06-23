"use client";

import { Card, Tag, Typography, Space, Image } from "antd";
import {
  EyeOutlined,
  LikeOutlined,
  MessageOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useRouter } from "next/navigation";
import type { HotArticle } from "@/lib/types";

const { Text, Paragraph } = Typography;

interface ArticleCardProps {
  article: HotArticle;
}

function formatCount(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return `${n}`;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const router = useRouter();
  const coverImage = article.images?.[0];

  return (
    <Card
      hoverable
      style={{ marginBottom: 16, borderRadius: 12, overflow: "hidden" }}
      bodyStyle={{ padding: 16 }}
      onClick={() => router.push(`/article/${article.id}`)}
    >
      <div style={{ display: "flex", gap: 16 }}>
        {/* 封面图 */}
        {coverImage && (
          <div style={{ width: 140, height: 100, flexShrink: 0, borderRadius: 8, overflow: "hidden" }}>
            <Image
              src={coverImage.url}
              alt={article.title}
              width={140}
              height={100}
              style={{ objectFit: "cover" }}
              preview={false}
              fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAwAB/9mGkwAAAABJRU5ErkJggg=="
            />
          </div>
        )}

        {/* 内容 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ fontSize: 16, fontWeight: 500, marginBottom: 8, lineHeight: 1.5 }}
          >
            {article.title}
          </Paragraph>
          {article.summary && (
            <Paragraph
              type="secondary"
              ellipsis={{ rows: 2 }}
              style={{ fontSize: 13, marginBottom: 8 }}
            >
              {article.summary}
            </Paragraph>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 4 }}>
            <Space size={6} wrap>
              <Tag color="blue" style={{ margin: 0, fontSize: 11 }}>
                {article.platform.name}
              </Tag>
              {article.author_name && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <UserOutlined style={{ marginRight: 2 }} />
                  {article.author_name}
                </Text>
              )}
            </Space>

            <Space size={12}>
              {article.read_count > 0 && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <EyeOutlined style={{ marginRight: 2 }} />
                  {formatCount(article.read_count)}
                </Text>
              )}
              {article.like_count > 0 && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <LikeOutlined style={{ marginRight: 2 }} />
                  {formatCount(article.like_count)}
                </Text>
              )}
              {article.comment_count > 0 && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <MessageOutlined style={{ marginRight: 2 }} />
                  {formatCount(article.comment_count)}
                </Text>
              )}
            </Space>
          </div>
        </div>
      </div>
    </Card>
  );
}
