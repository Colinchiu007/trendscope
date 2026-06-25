"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Layout, Form, Input, Button, Typography, Card, message, Space } from "antd";
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined, FireOutlined } from "@ant-design/icons";
import { useRegister } from "@/hooks/useAuth";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function RegisterPage() {
  const router = useRouter();
  const register = useRegister();

  const onFinish = (values: any) => {
    register.mutate(
      {
        username: values.username,
        password: values.password,
        email: values.email || undefined,
        phone: values.phone || undefined,
      },
      {
        onSuccess: (res: any) => {
          if (res.code === 0) {
            message.success("注册成功，请登录");
            router.push("/user/login");
          } else {
            message.error(res.message || "注册失败");
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
            注册
          </Title>

          <Form onFinish={onFinish} size="large" autoComplete="off">
            <Form.Item
              name="username"
              rules={[
                { required: true, message: "请输入用户名" },
                { min: 3, message: "至少3个字符" },
                { pattern: /^[a-zA-Z0-9_一-鿿]+$/, message: "只支持字母、数字、下划线和中文" },
              ]}
            >
              <Input prefix={<UserOutlined />} placeholder="用户名" />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[
                { required: true, message: "请输入密码" },
                { min: 8, message: "密码至少8位" },
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="密码（至少8位）" />
            </Form.Item>
            <Form.Item
              name="passwordConfirm"
              dependencies={["password"]}
              rules={[
                { required: true, message: "请确认密码" },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue("password") === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error("两次输入密码不一致"));
                  },
                }),
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
            </Form.Item>
            <Form.Item name="email" rules={[{ type: "email", message: "邮箱格式不正确" }]}>
              <Input prefix={<MailOutlined />} placeholder="邮箱（选填）" />
            </Form.Item>
            <Form.Item name="phone" rules={[{ pattern: /^1\d{10}$/, message: "手机号格式不正确" }]}>
              <Input prefix={<PhoneOutlined />} placeholder="手机号（选填）" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" block loading={register.isPending}>
                注册
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: "center" }}>
            <Text type="secondary" style={{ fontSize: 13 }}>
              已有账号？<Link href="/user/login">立即登录</Link>
            </Text>
          </div>
        </Card>
      </Content>
    </Layout>
  );
}
