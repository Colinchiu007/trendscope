"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Layout, Input, Typography, Space, Tag, Spin, Empty } from "antd";
import { SearchOutlined, ArrowLeftOutlined, FireOutlined } from "@ant-design/icons";
import { useSearchArticles } from "@/hooks/useArticles";
import { ArticleCard } from "@/components/article/ArticleCard";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") || "";
  const [query, setQuery] = useState(initialQ);
  const [page, setPage] = useState(1);

  const { data, isLoading } = useSearchArticles(initialQ, undefined, page);
  const items = data?.data?.items || [];
  const total = data?.pagination?.total || 0;

  const handleSearch = (value: string) => {
    setQuery(value);
    if (value.trim()) {
      router.push(`/search?q=${encodeURIComponent(value.trim())}`);
    }
  };

  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f5f5" }}>
      <Header
        style={{
          background: "#fff",
          display: "flex",
          alignItems: "center",
          borderBottom: "1px solid #f0f0f0",
          padding: "0 24px",
          gap: 12,
        }}
      >
        <FireOutlined
          style={{ fontSize: 20, color: "#f5222d", cursor: "pointer" }}
          onClick={() => router.push("/")}
        />
        <Input.Search
          placeholder="搜索热榜话题和文章..."
          defaultValue={initialQ}
          onSearch={handleSearch}
          enterButton={<SearchOutlined />}
          size="large"
          style={{ maxWidth: 480 }}
          allowClear
        />
      </Header>

      <Content style={{ padding: "16px 24px" }}>
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          {initialQ && (
            <div style={{ marginBottom: 16 }}>
              <Text type="secondary">
                搜索 &quot;{initialQ}&quot; 共找到 {total} 条结果
              </Text>
            </div>
          )}

          {isLoading ? (
            <div style={{ textAlign: "center", padding: "60px 0" }}>
              <Spin size="large" />
            </div>
          ) : items.length > 0 ? (
            items.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))
          ) : (
            initialQ && (
              <Empty
                description="未找到相关内容"
                style={{ padding: "60px 0" }}
              />
            )
          )}

          {!initialQ && (
            <div style={{ textAlign: "center", padding: "80px 0", color: "#999" }}>
              <SearchOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <p>输入关键词搜索热榜话题和文章</p>
            </div>
          )}
        </div>
      </Content>
    </Layout>
  );
}
