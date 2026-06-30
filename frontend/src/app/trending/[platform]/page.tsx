"use client";

import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Layout, Typography, Button, Space, List, Tag, Pagination, Result, Spin, Modal } from "antd";
import {
  ArrowLeftOutlined, FireOutlined, CaretUpOutlined,
  CaretDownOutlined, MinusOutlined, ThunderboltOutlined,
} from "@ant-design/icons";
import { usePlatformTrending, useTrendingHistory } from "@/hooks/useTrending";
import { PLATFORM_COLORS, PLATFORM_LOGOS } from "@/lib/constants";
import type { TrendingTopic, TrendHistoryData } from "@/lib/types";
import { TrendChart } from "@/components/trending/TrendChart";

const { Header, Content } = Layout;
const { Text, Title } = Typography;

const RANK_COLORS: Record<number, string> = { 1: "#ea444d", 2: "#ed702d", 3: "#eead3f" };

/** Render rank change indicator */
function RankChangeBadge({ change }: { change: number | null }) {
  if (change === null) {
    return (
      <Tag color="blue" style={{ fontSize: 10, lineHeight: "16px", padding: "0 4px", margin: 0, border: "none" }}>
        NEW
      </Tag>
    );
  }
  if (change > 0) {
    return (
      <span style={{ color: "#52c41a", fontSize: 13, fontWeight: 600, display: "inline-flex", alignItems: "center", gap: 1 }}>
        <CaretUpOutlined />{change > 1 ? change : ""}
      </span>
    );
  }
  if (change < 0) {
    return (
      <span style={{ color: "#ff4d4f", fontSize: 13, fontWeight: 600, display: "inline-flex", alignItems: "center", gap: 1 }}>
        <CaretDownOutlined />{change < -1 ? Math.abs(change) : ""}
      </span>
    );
  }
  return (
    <span style={{ color: "#d9d9d9", fontSize: 13, display: "inline-flex", alignItems: "center" }}>
      <MinusOutlined />
    </span>
  );
}

export default function PlatformTrendingPage() {
  const params = useParams();
  const router = useRouter();
  const platform = (params.platform as string) || "weibo";
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<'rank' | 'hot'>('rank');
  const pageSize = 30;

  // Trend chart modal state
  const [chartTopic, setChartTopic] = useState<{ id: number; title: string } | null>(null);
  const [chartOpen, setChartOpen] = useState(false);

  const { data, isLoading, isError, error, refetch } = usePlatformTrending(platform, page);
  const { data: historyData, isLoading: historyLoading } = useTrendingHistory(
    chartTopic?.id ?? 0,
    chartTopic && chartOpen,
  );

  const items: TrendingTopic[] = data?.data?.items || [];
  const total = data?.pagination?.total || 0;
  const sortedItems = sortBy === 'hot'
    ? [...items].sort((a, b) => (b.hot_value_norm || 0) - (a.hot_value_norm || 0))
    : items;
  const accentColor = PLATFORM_COLORS[platform] || "#666";
  const logoUrl = PLATFORM_LOGOS[platform] || "/logos/default.png";

  const handleShowChart = useCallback((topic: TrendingTopic) => {
    setChartTopic({ id: topic.id, title: topic.title });
    setChartOpen(true);
  }, []);

  const chartHistory: TrendHistoryData | undefined = historyData?.data;

  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f5f5" }}>
      <Header style={{
        background: "#fff", display: "flex", alignItems: "center",
        borderBottom: "1px solid #f0f0f0", padding: "0 24px", height: 56, gap: 12,
      }}>
        <Button type="text" icon={<ArrowLeftOutlined />}
          onClick={() => router.push("/")} />
        <img src={logoUrl} alt="" style={{ width: 22, height: 22, borderRadius: 4 }}
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
        <Title level={5} style={{ margin: 0 }}>{platform}热榜</Title>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
          <Button size='small' type={sortBy === 'rank' ? 'primary' : 'text'}
            onClick={() => setSortBy('rank')}>排名</Button>
          <Button size='small' type={sortBy === 'hot' ? 'primary' : 'text'}
            onClick={() => setSortBy('hot')}>热度</Button>
        </div>
      </Header>

      <Content style={{ padding: "16px 24px" }}>
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          {isError ? (
            <Result
              status="error"
              title="加载失败"
              subTitle={error instanceof Error ? error.message : "无法获取热榜数据，请稍后重试"}
              extra={
                <Button type="primary" onClick={() => refetch()}>
                  重新加载
                </Button>
              }
            />
          ) : (
            <>
              <List
                loading={isLoading}
                dataSource={sortedItems}
                renderItem={(item: TrendingTopic, idx: number) => {
                  const rank = (page - 1) * pageSize + idx + 1;
                  const rankColor = RANK_COLORS[rank] || "#f0f0f0";
                  const rankTextColor = RANK_COLORS[rank] ? "#fff" : "#999";
                  return (
                    <List.Item
                      style={{ cursor: "pointer", padding: "10px 12px", borderRadius: 8, transition: "all 0.2s" }}
                      className="list-item-hover"
                      onClick={() => item.topic_url && window.open(item.topic_url, "_blank")}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 12, width: "100%" }}>
                        {/* Rank number */}
                        <div style={{
                          width: 26, height: 26, borderRadius: 6, flexShrink: 0,
                          background: rankColor, color: rankTextColor,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 12, fontWeight: 700,
                        }}>
                          {rank}
                        </div>

                        {/* Rank change indicator */}
                        <div style={{ width: 40, flexShrink: 0, display: "flex", justifyContent: "center" }}>
                          <RankChangeBadge change={item.rank_change} />
                        </div>

                        {/* Title + meta */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <Text style={{ fontSize: 15 }}>{item.title}</Text>
                          <div style={{ marginTop: 4 }}>
                            {item.hot_value && (
                              <Tag icon={<FireOutlined />} color={accentColor} style={{ fontSize: 11 }}>
                                {item.hot_value}
                              </Tag>
                            )}
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              {item.platform?.name}
                            </Text>
                          </div>
                        </div>

                        {/* Trend chart trigger */}
                        <Button
                          type="text"
                          size="small"
                          icon={<ThunderboltOutlined />}
                          onClick={(e) => { e.stopPropagation(); handleShowChart(item); }}
                          style={{ color: "#bbb", flexShrink: 0 }}
                          title="查看7天趋势"
                        />
                      </div>
                    </List.Item>
                  );
                }}
              />
              {total > pageSize && (
                <div style={{ textAlign: "center", marginTop: 16 }}>
                  <Pagination current={page} pageSize={pageSize} total={total}
                    onChange={setPage} showSizeChanger={false} size="small" />
                </div>
              )}
            </>
          )}
        </div>
      </Content>

      {/* 7-day trend modal */}
      <Modal
        title={chartTopic?.title}
        open={chartOpen}
        onCancel={() => setChartOpen(false)}
        footer={null}
        width={640}
        destroyOnClose
      >
        {historyLoading ? (
          <div style={{ textAlign: "center", padding: "40px 0" }}>
            <Spin />
          </div>
        ) : chartHistory?.history && chartHistory.history.length > 1 ? (
          <TrendChart history={chartHistory.history} />
        ) : (
          <div style={{ textAlign: "center", padding: "40px 0", color: "#999" }}>
            暂无足够的历史数据生成趋势图
          </div>
        )}
      </Modal>

      <style>{`.list-item-hover:hover { background: #f0f0f0; }`}</style>
    </Layout>
  );
}
