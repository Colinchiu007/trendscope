"use client";

import { Card, Descriptions, Form, Input, Button, message, Spin, Avatar } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { useProfile } from "@/hooks/useAuth";

export default function ProfilePage() {
  const { data: profile, isLoading } = useProfile();
  const user = profile?.data;

  if (isLoading) return <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div>;
  if (!user) return <p style={{ textAlign: "center", color: "#999" }}>请先登录</p>;

  return (
    <div>
      <Card style={{ borderRadius: 12 }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <Avatar size={80} icon={<UserOutlined />} src={user.avatar_url} style={{ marginBottom: 12 }} />
          <h3>{user.nickname || user.username}</h3>
          <p style={{ color: "#999", fontSize: 13 }}>{user.role === "admin" ? "管理员" : "普通用户"}</p>
        </div>

        <Descriptions column={1} labelStyle={{ width: 80, color: "#666" }} size="small">
          <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{user.email || "未设置"}</Descriptions.Item>
          <Descriptions.Item label="手机号">{user.phone || "未设置"}</Descriptions.Item>
          <Descriptions.Item label="注册时间">{user.created_at ? new Date(user.created_at).toLocaleDateString("zh-CN") : ""}</Descriptions.Item>
        </Descriptions>

        <Form layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item label="昵称">
            <Input placeholder={user.nickname || "设置昵称"} />
          </Form.Item>
          <Form.Item label="邮箱">
            <Input placeholder={user.email || "绑定邮箱"} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" block disabled>保存修改（开发中）</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
