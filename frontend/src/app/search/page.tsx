"use client";

import { useState, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Layout, Input, Typography, Tabs, Spin, Empty, Tag, Button, Collapse, Checkbox, Space, Badge } from "antd";
import {
  SearchOutlined,
  FireOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  FilterOutlined,
} from "@ant-design/icons";
import { useSearchArticles, useLast30daysSearch } from "@/hooks/useArticles";
import { ArticleCard } from "@/components/article/ArticleCard";
import { Last30daysResultCard } from "@/components/article/Last30daysResultCard";
import { usePlatforms } from "@/hooks/useTrending";

const { Header, Content } = Layout;
const { Text } = Typography;

/** 高亮匹配关键词 */
function HighlightText({ text, keyword }: { text: string; keyword: string }) {
  if (!keyword.trim()) return <>{text}</>;
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const parts = text.split(new RegExp(`(${escaped})`, "gi"));
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === keyword.toLowerCase()
          ? <mark key={i} style={{ background: "#fff3b0", padding: "0 2px", borderRadius: 2, fontWeight: 500 }}>{part}</mark>
          : part,
      )}
    </>
  );
}

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") || "";
  const [query, setQuery] = useState(initialQ);
  const [activeTab, setActiveTab] = useState("local");
  const [filterOpen, setFilterOpen] = useState(false);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);

  const { data: platformsData } = usePlatforms();
  const allPlatforms = platformsData?.data?.platforms || [];

  // Search with platform filter
  const platformsParam = selectedPlatforms.length > 0 ? selectedPlatforms.join(",") : undefined;

  const { data: localData, isLoading: localLoading } = useSearchArticles(initialQ, platformsParam, 1);
  const { data: last30daysData, isLoading: l30Loading, error: l30Error } = useLast30daysSearch(
    activeTab === "last30days" ? initialQ : ""
  );

  const localItems = localData?.data?.items || [];
  const localTotal = localData?.pagination?.total || 0;
  const l30Results = last30daysData?.data?.results || [];
  const l30Total = last30daysData?.data?.total || 0;
  const l30Sources = last30daysData?.data?.sources || [];
  const l30Errors = last30daysData?.data?.errors || {};

  // Platform filter badge
  const filterActive = selectedPlatforms.length > 0;

  const handleSearch = (value: string) => {
    setQuery(value);
    if (value.trim()) {
      router.push(`/search?q=${encodeURIComponent(value.trim())}`);
    }
  };

  const handlePlatformToggle = (code: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code],
    );
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
            <>
              {/* ── 筛选面板 ── */}
              <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <Button
                  size="small"
                  icon={<FilterOutlined />}
                  onClick={() => setFilterOpen(!filterOpen)}
                  type={filterActive ? "primary" : "default"}
                >
                  筛选{filterActive && <Badge count={selectedPlatforms.length} size="small" style={{ marginLeft: 4 }} />}
                </Button>
                {filterActive && (
                  <Button size="small" type="text" onClick={() => setSelectedPlatforms([])}>
                    清除筛选
                  </Button>
                )}
              </div>

              {filterOpen && allPlatforms.length > 0 && (
                <div
                  style={{
                    background: "#fff", borderRadius: 8, padding: "12px 16px", marginBottom: 16,
                    border: "1px solid #f0f0f0",
                  }}
                >
                  <Text strong style={{ fontSize: 13, display: "block", marginBottom: 8 }}>平台筛选</Text>
                  <Checkbox.Group
                    value={selectedPlatforms}
                    style={{ display: "flex", flexWrap: "wrap", gap: 8 }}
                  >
                    {allPlatforms.map((p) => (
                      <Checkbox key={p.code} value={p.code} onChange={() => handlePlatformToggle(p.code)}
                        style={{ fontSize: 13 }}>
                        {p.name}
                      </Checkbox>
                    ))}
                  </Checkbox.Group>
                </div>
              )}

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
                            <div key={article.id} style={{ marginBottom: 16 }}>
                              <ArticleCard article={article} highlightKeyword={initialQ} />
                            </div>
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
                          <Empty description="跨源搜索暂时不可用" style={{ padding: "60px 0" }} />
                        ) : (
                          <Empty description="未搜索到跨源结果" style={{ padding: "60px 0" }} />
                        )}

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
            </>
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
                                      