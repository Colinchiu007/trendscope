"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Layout, Typography, Space, Input, Button, Avatar, Skeleton, Card } from "antd";
import { FireOutlined, SearchOutlined, UserOutlined, AppstoreOutlined } from "@ant-design/icons";
import { usePlatforms } from "@/hooks/useTrending";
import { useProfile } from "@/hooks/useAuth";
import { HotListCard } from "@/components/trending/HotListCard";
import { isLoggedIn } from "@/lib/auth";

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

export default function HomePage() {
  const router = useRouter();
  const [searchValue, setSearchValue] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");

  const loggedIn = typeof window !== "undefined" ? isLoggedIn() : false;
  const { data: profileData } = useProfile();
  const { data: platformsData, isLoading } = usePlatforms();

  const platforms = platformsData?.data?.platforms || [];
  const categories = ["all", ...new Set(platforms.map(p => p.category).filter(Boolean))];
  const filteredPlatforms = activeCategory === "all" ? platforms : platforms.filter(p => p.category === activeCategory);

  const handleSearch = (value: string) => {
    if (value.trim()) {
      router.push(`/search?q=${encodeURIComponent(value.trim())}`);
    }
  };

  const renderSkeletonGrid = () => (
    <div className="platform-grid">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <Card key={i} style={{ borderRadius: 12, height: 180 }}>
          <Skeleton active avatar paragraph={{ rows: 2 }} />
        </Card>
      ))}
    </div>
  );

  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f5f5" }}>
      <Header
        style={{
          background: "#fff",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          borderBottom: "1px solid #f0f0f0", padding: "0 24px",
          position: "sticky", top: 0, zIndex: 100, gap: 16,
          height: 56,
        }}
      >
        <Space>
          <FireOutlined style={{ fontSize: 22, color: "#f5222d", cursor: "pointer" }}
            onClick={() => router.push("/")} />
          <Title level={5} style={{ margin: 0 }}>热榜</Title>
          <span style={{ fontSize: 11, color: "#999", background: "#f5f5f5", padding: "2px 8px", borderRadius: 4 }}>Beta</span>
        </Space>

        <Input.Search
          placeholder="搜索热榜..."
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          onSearch={handleSearch}
          style={{ maxWidth: 280 }}
          allowClear
          enterButton={<SearchOutlined />}
        />

        {loggedIn ? (
          <Button type="text" icon={<Avatar size={28} icon={<UserOutlined />}
            src={profileData?.data?.avatar_url} />}
            onClick={() => router.push("/user/profile")} style={{ padding: 0 }} />
        ) : (
          <Button type="primary" ghost size="small" onClick={() => router.push("/user/login")}>登录</Button>
        )}
      </Header>

      <Content style={{ padding: "20px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          {/* Category filter tabs */}
          {!isLoading && categories.length > 1 && (
            <div style={{ marginBottom: 20, display: "flex", gap: 8, flexWrap: "wrap" }}>
              {categories.map((cat) => (
                <button key={cat}
                  onClick={() => setActiveCategory(cat)}
                  style={{
                    padding: "6px 18px", borderRadius: 20, cursor: "pointer", fontSize: 13,
                    border: activeCategory === cat ? "none" : "1px solid #d9d9d9",
                    background: activeCategory === cat ? "#f5222d" : "#fff",
                    color: activeCategory === cat ? "#fff" : "#666",
                    fontWeight: activeCategory === cat ? 600 : 400,
                    transition: "all 0.2s",
                  }}
                >
                  {cat === "all" ? <><AppstoreOutlined /> 全部</> : cat}
                </button>
              ))}
            </div>
          )}
          {/* Platform grid */}
          {isLoading ? (
            renderSkeletonGrid()
          ) : platforms.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px 0", color: "#ccc" }}>
              <Title level={4} type="secondary">暂无平台数据</Title>
            </div>
          ) : (
            <div className="platform-grid">
              {filteredPlatforms.map((p) => (
                <HotListCard key={p.code} platformCode={p.code} platformName={p.name} />
              ))}
            </div>
          )}
        </div>
      </Content>

      <Footer style={{ textAlign: "center", color: "#bbb", fontSize: 12 }}>
        TrendScope 热榜 &copy;2025 - 多平台热榜聚合引擎
      </Footer>

      <style>{`
        .platform-grid {
          display: grid;
          grid-template-columns: 1fr;
          grid-auto-rows: 1fr;
          gap: 20px;
          min-width: 0;
        }
        .platform-grid > * { min-width: 0; width: 100%; }
        @media (min-width: 560px) { .platform-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (min-width: 800px) { .platform-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (min-width: 1100px) { .platform-grid { grid-template-columns: repeat(4, 1fr); } }
        .hot-list-item:hover { background: #f5f5f5; }
      `}</style>
    </Layout>
  );
}
