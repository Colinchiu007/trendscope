"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Layout, Typography, Button, Space, Badge } from "antd";
import { ArrowLeftOutlined, FireOutlined } from "@ant-design/icons";
import { usePlatformTrending } from "@/hooks/useTrending";
import { HotList } from "@/components/trending/HotList";
import { PLATFORMS } from "@/lib/constants";

const { Header, Content } = Layout;
const { Title } = Typography;

const PLATFORM_NAMES: Record<string, string> = {};
PLATFORMS.forEach((p) => {
  PLATFORM_NAMES[p.code] = p.name;
});

export default function PlatformTrendingPage() {
  const params = useParams();
  const router = useRouter();
  const platform = (params.platform as string) || "weibo";
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data, isLoading } = usePlatformTrending(platform, page);
  const trendingData = data?.data;
  const items = trendingData?.items || [];
  const total = data?.pagination?.total || 0;

  const platformName = PLATFORM_NAMES[platform] || platform;

  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f5f5" }}>
      <Header
        style={{
          background: "#fff",
          display: "flex",
          alignItems: "center",
          borderBottom: "1px solid #f0f0f0",
          padding: "0 24px",
        }}
      >
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => router.push("/")}
          />
          <FireOutlined style={{ fontSize: 20, color: "#f5222d" }} />
          <Title level={5} style={{ margin: 0 }}>
            {platformName}热榜
          </Title>
        </Space>
      </Header>

      <Content style={{ padding: "16px 24px" }}>
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <HotList
            items={items}
            loading={isLoading}
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={setPage}
          />
        </div>
      </Content>
    </Layout>
  );
}
