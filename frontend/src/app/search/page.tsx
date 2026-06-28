"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Layout, Input, Typography, Tabs, Spin, Empty, Tag } from "antd";
import {
  SearchOutlined,
  FireOutlined,
  GlobalOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import { useSearchArticles, useLast30daysSearch } from "@/hooks/useArticles";
import { ArticleCard } from "@/components/article/ArticleCard";
import { Last30daysResultCard } from "@/components/article/Last30daysResultCard";

const { Header, Content } = Layout;
const { Text } = Typography;

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") || "";
  const [query, setQuery] = useState(initialQ);
  const [activeTab, setActiveTab] = useState("local");

  const { data: localData, isLoading: localLoading } = useSearchArticles(initialQ, undefined, 1);
  const { data: last30daysData, isLoading: l30Loading, error: l30Error } = useLast30daysSearch(
    activeTab === "last30days" ? initialQ : ""
  );

  const localItems = localData?.data?.items || [];
  const localTotal = localData?.pagination?.total || 0;
  const l30Results = last30daysData?.data?.results || [];
  const l30Total = last30daysData?.data?.total || 0;
  const l30Sources = last30daysData?.data?.sources || [];
  const l30Errors = last30daysData?.data?.errors || {};

  const handleSearch = (value: string) => {
    setQuery(value);
    if (value.trim()) {
      router.push(`/search?q=${encodeURIComponent(value.trim())}`);
    }
  };

  const sourceIcons: Record<string, React.ReactNode> = {
    reddit: <Tag color="#FF4500" style={{ fontSize: 10, margin: 0 }}>Reddit</Tag>,
    hackernews: <Tag color="#FF6600" style={{ fontSize: 10, margin: 0 }}>HN</Tag>,
    github: <Tag style={{ fontSize: 10, margin: 0, background: "#24292F", color: "#fff", border: "none" }}>GitHub</Tag>,
    polymarket: <Tag color="#0E76FD" style={{ fontSize: 10, margin: 0 }}>Polymarket</Tag>,
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
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              style={{ marginBottom: 16 }}
              items={[
                {
                  key: "local",
                  label: (
                    <span>
                      <DatabaseOutlined /> 本地文章
                      {localTotal > 0 && <span style={{ marginLeft: 4, fontSize: 12, color: "#999" }}>({localTotal})</span>}
                    </span>
                  ),
                  children: (
                    <>
                      {localLoading ? (
                        <div style={{ textAlign: "center", padding: "60px 0" }}>
                          <Spin size="large" />
                        </div>
                      ) : localItems.length > 0 ? (
                        localItems.map((article: any) => (
                          <ArticleCard key={article.id} article={article} />
                        ))
                      ) : (
                        <Empty description="未找到相关内容" style={{ padding: "60px 0" }} />
                      )}
                    </>
                  ),
                },
                {
                  key: "last30days",
                  label: (
                    <span>
                      <GlobalOutlined /> 跨源搜索
                      {l30Total > 0 && <span style={{ marginLeft: 4, fontSize: 12, color: "#999" }}>({l30Total})</span>}
                    </span>
                  ),
                  children: (
                    <>
                      {/* 活跃的搜索源指示 */}
                      {l30Sources.length > 0 && !l30Loading && (
                        <div style={{ marginBottom: 12, display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>数据源:</Text>
                          {l30Sources.map((s) => (
                            <span key={s}>{sourceIcons[s] || s}</span>
                          ))}
                        </div>
                      )}

                      {l30Loading ? (
                        <div style={{ textAlign: "center", padding: "60px 0" }}>
                          <Spin size="large" tip="正在跨源搜索..." />
                        </div>
                      ) : l30Results.length > 0 ? (
                        l30Results.map((item) => (
                          <Last30daysResultCard key={item.item_id} item={item} />
                        ))
                      ) : l30Error ? (
                        <Empty
                          description="跨源搜索暂时不可用"
                          style={{ padding: "60px 0" }}
                        />
                      ) : (
                        <Empty
                          description="未搜索到跨源结果"
                          style={{ padding: "60px 0" }}
                        />
                      )}

                      {/* 错误提示 */}
                      {Object.keys(l30Errors).length > 0 && (
                        <div style={{ marginTop: 16, padding: 12, background: "#fff2f0", borderRadius: 8, border: "1px solid #ffccc7" }}>
                          <Text type="danger" style={{ fontSize: 12 }}>
                            以下数据源异常: {Object.entries(l30Errors).map(([src, err]) => `${src}(${err})`).join(", ")}
                          </Text>
                        </div>
                      )}
                    </>
                  ),
                },
              ]}
            />
          )}

          {!initialQ && (
            <div style={{ textAlign: "center", padding: "80px 0", color: "#999" }}>
              <SearchOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <p>输入关键词搜索热榜话题和文章</p>
              <p style={{ fontSize: 13, marginTop: 8 }}>
                支持 Reddit · Hacker News · GitHub · Polymarket 跨源搜索
              </p>
            </div>
          )}
        </div>
      </Content>
    </Layout>
  );
}