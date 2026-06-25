"use client";

import { Layout, Menu, Typography, Space } from "antd";
import { UserOutlined, HeartOutlined, BellOutlined, FireOutlined, LogoutOutlined } from "@ant-design/icons";
import { useRouter, usePathname } from "next/navigation";
import { useLogout, useProfile } from "@/hooks/useAuth";
import { useEffect } from "react";
import { getToken } from "@/lib/auth";

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

export default function UserAppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: profileData } = useProfile();
  const logout = useLogout();

  useEffect(() => {
    if (!getToken()) router.replace("/user/login");
  }, [router]);

  const menuItems = [
    { key: "/user/profile", icon: <UserOutlined />, label: "个人信息" },
    { key: "/user/favorites", icon: <HeartOutlined />, label: "我的收藏" },
    { key: "/user/subscriptions", icon: <BellOutlined />, label: "订阅管理" },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ background: "#fff", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #f0f0f0", padding: "0 24px" }}>
        <Space>
          <FireOutlined style={{ fontSize: 20, color: "#f5222d", cursor: "pointer" }} onClick={() => router.push("/")} />
          <Title level={5} style={{ margin: 0 }}>热榜 TrendScope</Title>
        </Space>
        {profileData?.data && (
          <Space>
            <span style={{ color: "#666", fontSize: 13 }}>{profileData.data.nickname || profileData.data.username}</span>
            <LogoutOutlined style={{ cursor: "pointer", color: "#999" }} onClick={logout} />
          </Space>
        )}
      </Header>
      <Layout>
        <Sider width={200} style={{ background: "#fafafa", borderRight: "1px solid #f0f0f0" }} breakpoint="sm" collapsedWidth={0}>
          <Menu
            mode="inline"
            selectedKeys={[pathname]}
            items={menuItems}
            onClick={({ key }) => router.push(key)}
            style={{ borderRight: 0, marginTop: 16 }}
          />
        </Sider>
        <Content style={{ padding: 24, background: "#f5f5f5" }}>
          <div style={{ maxWidth: 720, margin: "0 auto" }}>{children}</div>
        </Content>
      </Layout>
    </Layout>
  );
}
