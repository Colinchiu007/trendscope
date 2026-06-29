"use client";

import { useState } from "react";
import { Card, Descriptions, Form, Input, Button, message, Spin, Avatar } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { useProfile } from "@/hooks/useAuth";
import { apiClient } from "@/lib/api-client";

export default function ProfilePage() {
  const { data: profile, isLoading } = useProfile();
  const user = profile?.data;
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  if (isLoading) return <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div>;
  if (!user) return <p style={{ textAlign: "center", color: "#999" }}>请先登录</p>;

  const handleSave = async (values: { nickname?: string; email?: string }) => {
    setSaving(true);
    try {
      const res: any = await apiClient.put("/user/profile", values);
      if (res.code === 0) {
        message.success("保存成功");
      } else {
        message.error(res.message || "保存失败");
      }
    } catch {
      message.error("网络错误，保存失败");
    } finally {
      setSaving(false);
    }
  };

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

        <Form form={form} layout="vertical" style={{ marginTop: 24 }} onFinish={handleSave}>
          <Form.Item label="昵称" name="nickname">
            <Input placeholder={user.nickname || "设置昵称"} />
          </Form.Item>
          <Form.Item label="邮箱" name="email">
            <Input placeholder={user.email || "绑定邮箱"} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={saving}>
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
