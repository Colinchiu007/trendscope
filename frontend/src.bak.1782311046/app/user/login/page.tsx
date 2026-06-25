"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Layout, Form, Input, Button, Typography, Card, message, Space, Tabs } from "antd";
import { UserOutlined, LockOutlined, PhoneOutlined, FireOutlined } from "@ant-design/icons";
import { useLogin } from "@/hooks/useAuth";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const [mode, setMode] = useState<"password" | "sms">("password");

  const onFinish = (values: any) => {
    login.mutate(
      { account: values.account, password: values.password },
      {
        onSuccess: (res: any) => {
          if (res.code === 0) {
            message.success("登录成功");
            router.push("/");
          } else {
            message.error(res.message || "登录失败");
          }
        },
        onError: () => message.error("网络错误，请稍后重试"),
      }
    );
  };

  return (
    <Layout style={{ minHeight: "100vh", background: "#f0f2f5" }}>
      <Header style={{ background: "#fff", textAlign: "center", borderBottom: "1px solid #f0f0f0" }}>
        <Space>
          <FireOutlined style={{ fontSize: 24, color: "#f5222d" }} />
          <Title level={4} style={{ margin: 0, lineHeight: "64px" }}>
            热榜 TrendScope
          </Title>
        </Space>
      </Header>

      <Content style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: 24 }}>
        <Card style={{ width: 400, borderRadius: 12, boxShadow: "0 2px 16px rgba(0,0,0,0.08)" }}>
          <Title level={5} style={{ textAlign: "center", marginBottom: 24 }}>
            登录
          </Title>

          <Tabs activeKey={mode} onChange={(k) => setMode(k as any)} centered items={[
            { key: "password", label: "密码登录" },
            { key: "sms", label: "短信登录" },
          ]} />

          {mode === "password" ? (
            <Form onFinish={onFinish} size="large" autoComplete="off">
              <Form.Item name="account" rules={[{ required: true, message: "请输入用户名/邮箱/手机号" }]}>
                <Input prefix={<UserOutlined />} placeholder="用户名 / 邮箱 / 手机号" />
              </Form.Item>
              <Form.Item name="password" rules={[{ required: true, message: "请输入密码" }]}>
                <Input.Password prefix={<LockOutlined />} placeholder="密码" />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" block loading={login.isPending}>
                  登录
                </Button>
              </Form.Item>
            </Form>
          ) : (
            <Form size="large">
              <Form.Item name="phone" rules={[{ required: true, message: "请输入手机号" }]}>
                <Input prefix={<PhoneOutlined />} placeholder="手机号" />
              </Form.Item>
              <Form.Item name="code" rules={[{ required: true, message: "请输入验证码" }]}>
                <Input.Search
                  placeholder="验证码"
                  enterButton="获取验证码"
                  onSearch={() => {}}
                />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" block disabled>
                  登录
                </Button>
              </Form.Item>
            </Form>
          )}

          <div style={{ textAlign: "center" }}>
            <Text type="secondary" style={{ fontSize: 13 }}>
              还没有账号？<Link href="/user/register">立即注册</Link>
            </Text>
          </div>
        </Card>
      </Content>
    </Layout>
  );
}
