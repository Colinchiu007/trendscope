"use client";

import { useParams, useRouter } from "next/navigation";
import { Layout, Typography, Button, Space, Image, Tag, Divider, Spin } from "antd";
import {
  ArrowLeftOutlined,
  EyeOutlined,
  LikeOutlined,
  MessageOutlined,
  ShareAltOutlined,
  LinkOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useArticle } from "@/hooks/useArticles";

const { Header, Content } = Layout;
const { Title, Text, Paragraph } = Typography;

function formatCount(n: number): string {
  if (n >= 100000000) return `${(n / 100000000).toFixed(1)}亿`;
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  return `${n}`;
}

export default function ArticleDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = parseInt((params.id as string) || "0", 10);

  const { data, isLoading, error } = useArticle(id);
  const article = data?.data;

  if (isLoading) {
    return (
      <div style={{ textAlign: "center", padding: "120px 0" }}>
        <Spin size="large" />
        <p style={{ marginTop: 16, color: "#999" }}>加载中...</p>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div style={{ textAlign: "center", padding: "120px 0" }}>
        <p style={{ color: "#999" }}>文章不存在或已下架</p>
        <Button onClick={() => router.push("/")}>返回首页</Button>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: "100vh", background: "#fff" }}>
      <Header
        style={{
          background: "#fff",
          display: "flex",
          alignItems: "center",
          borderBottom: "1px solid #f0f0f0",
          padding: "0 24px",
        }}
      >
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => router.back()}
        />
      </Header>

      <Content style={{ padding: "24px" }}>
        <article style={{ maxWidth: 720, margin: "0 auto" }}>
          {/* 标题 */}
          <Title level={3} style={{ marginBottom: 16, lineHeight: 1.4 }}>
            {article.title}
          </Title>

          {/* 元信息 */}
          <Space size={16} wrap style={{ marginBottom: 20, color: "#999", fontSize: 13 }}>
            {article.platform && (
              <Tag color="blue">{article.platform.name}</Tag>
            )}
            {article.author_name && (
              <span>
                <UserOutlined style={{ marginRight: 4 }} />
                {article.author_name}
              </span>
            )}
            {article.read_count > 0 && (
              <span>
                <EyeOutlined style={{ marginRight: 4 }} />
                {formatCount(article.read_count)}
              </span>
            )}
            {article.like_count > 0 && (
              <span>
                <LikeOutlined style={{ marginRight: 4 }} />
                {formatCount(article.like_count)}
              </span>
            )}
            {article.comment_count > 0 && (
              <span>
                <MessageOutlined style={{ marginRight: 4 }} />
                {formatCount(article.comment_count)}
              </span>
            )}
          </Space>

          <Divider />

          {/* 摘要 */}
          {article.summary && (
            <blockquote
              style={{
                borderLeft: "3px solid #3b82f6",
                paddingLeft: 16,
                color: "#666",
                fontSize: 15,
                lineHeight: 1.8,
                marginBottom: 24,
              }}
            >
              {article.summary}
            </blockquote>
          )}

          {/* 正文 */}
          {article.content_text && (
            <Paragraph
              style={{ fontSize: 16, lineHeight: 2, whiteSpace: "pre-wrap" }}
            >
              {article.content_text}
            </Paragraph>
          )}

          {/* 图片 */}
          {article.images && article.images.length > 0 && (
            <div style={{ margin: "24px 0" }}>
              {article.images.map((img, idx) => (
                <Image
                  key={idx}
                  src={img.url}
                  alt={`图片 ${idx + 1}`}
                  style={{ maxWidth: "100%", borderRadius: 8, marginBottom: 12 }}
                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wcAAwAB/9mGkwAAAABJRU5ErkJggg=="
                />
              ))}
            </div>
          )}

          <Divider />

          {/* 原文链接 */}
          {article.source_url && (
            <div style={{ textAlign: "center", padding: "16px 0" }}>
              <Button
                type="primary"
                icon={<LinkOutlined />}
                onClick={() => window.open(article.source_url, "_blank")}
                size="large"
              >
                查看原文 ({article.platform?.name || "未知平台"})
              </Button>
            </div>
          )}

          {/* 发布时间 */}
          {article.publish_at && (
            <div style={{ textAlign: "center", color: "#bbb", fontSize: 12, marginTop: 16 }}>
              发布于 {new Date(article.publish_at).toLocaleString("zh-CN")}
            </div>
          )}
        </article>
      </Content>
    </Layout>
  );
}
