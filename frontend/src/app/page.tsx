"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Layout, Tabs, Typography, Space, Badge, Input, Button, Avatar } from "antd";
import { FireOutlined, ThunderboltOutlined, SearchOutlined, UserOutlined } from "@ant-design/icons";
import { useAggregatedTrending, usePlatforms } from "@/hooks/useTrending";
import { useProfile } from "@/hooks/useAuth";
import { HotList } from "@/components/trending/HotList";
import { isLoggedIn } from "@/lib/auth";

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

export default function HomePage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("all");
  const [page, setPage] = useState(1);
  const pageSize = 30;

  const loggedIn = typeof window !== "undefined" ? isLoggedIn() : false;
  const { data: profileData } = useProfile();
  const { data: platformsData } = usePlatforms();
  const { data, isLoading } = useAggregatedTrending(
    activeTab === "all" ? undefined : activeTab,
    page
  );

  const platforms = platformsData?.data?.platforms || [];

  const tabItems = [
    {
      key: "all",
      label: (
        <span>
          <ThunderboltOutlined /> 全部
        </span>
      ),
    },
    ...platforms.slice(0, 12).map((p) => ({
      key: p.code,
      label: (
        <span>
          <Badge
            color={p.is_active ? "green" : "default"}
            style={{ width: 6, height: 6, marginRight: 4 }}
          />
          {p.name}
        </span>
      ),
    })),
  ];

  const trendingData = data?.data;
  const items = trendingData?.items || [];
  const total = data?.pagination?.total || 0;

  const handleSearch = (value: string) => {
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
          justifyContent: "space-between",
          borderBottom: "1px solid #f0f0f0",
          padding: "0 24px",
          position: "sticky",
          top: 0,
          zIndex: 100,
          gap: 16,
        }}
      >
        <Space>
          <FireOutlined
            style={{ fontSize: 24, color: "#f5222d", cursor: "pointer" }}
            onClick={() => router.push("/")}
          />
          <Title level={4} style={{ margin: 0 }}>
            热榜 TrendScope
          </Title>
          <span
            style={{
              fontSize: 11,
              color: "#999",
              background: "#f5f5f5",
              padding: "2px 8px",
              borderRadius: 4,
            }}
          >
            Beta
          </span>
        </Space>

        <Input.Search
          placeholder="搜索热榜..."
          onSearch={handleSearch}
          style={{ maxWidth: 300 }}
          allowClear
          enterButton={<SearchOutlined />}
        />

        {loggedIn ? (
          <Button
            type="text"
            icon={<Avatar size={28} icon={<UserOutlined />} src={profileData?.data?.avatar_url} />}
            onClick={() => router.push("/user/profile")}
            style={{ padding: 0 }}
          />
        ) : (
          <Button type="primary" ghost size="small" onClick={() => router.push("/user/login")}>
            登录
          </Button>
        )}
      </Header>

      <Content style={{ padding: "16px 24px" }}>
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <Tabs
            activeKey={activeTab}
            onChange={(key) => {
              setActiveTab(key);
              setPage(1);
            }}
            items={tabItems}
            size="large"
            style={{ marginBottom: 8 }}
          />

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

      <Footer style={{ textAlign: "center", color: "#bbb", fontSize: 12 }}>
        TrendScope 热榜 ©2025 - 多平台热榜聚合引擎
      </Footer>
    </Layout>
  );
}
