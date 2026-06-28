"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Layout, Typography, Button, Space, List, Tag, Pagination } from "antd";
import { ArrowLeftOutlined, FireOutlined } from "@ant-design/icons";
import { usePlatformTrending } from "@/hooks/useTrending";
import { PLATFORM_COLORS, PLATFORM_LOGOS } from "@/lib/constants";
import type { TrendingTopic } from "@/lib/types";

const { Header, Content } = Layout;
const { Text, Title } = Typography;

const RANK_COLORS: Record<number, string> = { 1: "#ea444d", 2: "#ed702d", 3: "#eead3f" };

export default function PlatformTrendingPage() {
  const params = useParams();
  const router = useRouter();
  const platform = (params.platform as string) || "weibo";
  const [page, setPage] = useState(1);
  const pageSize = 30;

  const { data, isLoading } = usePlatformTrending(platform, page);
  const items: TrendingTopic[] = data?.data?.items || [];
  const total = data?.pagination?.total || 0;
  const accentColor = PLATFORM_COLORS[platform] || "#666";
  const logoUrl = PLATFORM_LOGOS[platform] || "/logos/default.png";

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
      </Header>

      <Content style={{ padding: "16px 24px" }}>
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <List
            loading={isLoading}
            dataSource={items}
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
                    <div style={{
                      width: 26, height: 26, borderRadius: 6, flexShrink: 0,
                      background: rankColor, color: rankTextColor,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 12, fontWeight: 700,
                    }}>
                      {rank}
                    </div>
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
        </div>
      </Content>
      <style>{`.list-item-hover:hover { background: #f0f0f0; }`}</style>
    </Layout>
  );
}
