"use client";

// @ts-nocheck - skip type checks in this file (subscriptions feature is future work)

import { useState, useEffect } from "react";
import { Card, List, Button, Space, Tag, Spin, Empty, Typography, Popconfirm, message, Select, Checkbox } from "antd";
import { BellOutlined, PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { PLATFORMS } from "@/lib/constants";
import { apiClient } from "@/lib/api-client";

const { Text } = Typography;

interface Subscription {
  id: number;
  platform_id: number | null;
  keywords: string[];
  notify_email: boolean;
  notify_webpush: boolean;
  created_at: string;
}

export default function SubscriptionsPage() {
  const [loading, setLoading] = useState(false);
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [showCreate, setShowCreate] = useState(false);

  const fetchSubs = async () => {
    setLoading(true);
    try {
      const res: any = await apiClient.get("/user/subscriptions");
      if (res.code === 0) setSubs(res.data.items);
    } catch {
      message.error("加载订阅失败");
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchSubs(); }, []);

  const deleteSub = async (id: number) => {
    try {
      const res: any = await apiClient.delete(`/user/subscriptions/${id}`);
      if (res.code === 0) {
        message.success("已取消订阅");
        setSubs((prev) => prev.filter((s) => s.id !== id));
      }
    } catch { message.error("操作失败"); }
  };

  const createSub = async () => {
    try {
      const res: any = await apiClient.post("/user/subscriptions", {
        keywords: ["热点", "热搜"],
        notify_email: false,
      });
      if (res.code === 0) {
        message.success("订阅创建成功");
        setShowCreate(false);
        fetchSubs();
      }
    } catch { message.error("创建失败"); }
  };

  if (loading) return <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0 }}>
          <BellOutlined style={{ color: "#3b82f6", marginRight: 8 }} />
          订阅管理
        </h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>
          新建订阅
        </Button>
      </div>

      {showCreate && (
        <Card style={{ marginBottom: 16, borderRadius: 12, border: "1px solid #3b82f6" }}>
          <h4>新建订阅</h4>
          <p style={{ color: "#999", fontSize: 13, marginBottom: 16 }}>
            设置你关注的关键词，当匹配时我们会推送通知。
          </p>
          <Space style={{ width: "100%", justifyContent: "flex-end" }}>
            <Button onClick={() => setShowCreate(false)}>取消</Button>
            <Button type="primary" onClick={createSub}>创建</Button>
          </Space>
        </Card>
      )}

      {subs.length === 0 ? (
        <Card style={{ borderRadius: 12, textAlign: "center", padding: 40 }}>
          <Empty description="还没有订阅" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        </Card>
      ) : (
        <List
          dataSource={subs}
          renderItem={(sub) => (
            <Card hoverable style={{ marginBottom: 8, borderRadius: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <Space style={{ marginBottom: 4 }}>
                    {sub.platform_id && (
                      <Tag color="blue">
                        {PLATFORMS.find((p) => String(p.code) === String(sub.platform_id))?.name || `平台#${sub.platform_id}`}
                      </Tag>
                    )}
                    {sub.keywords.map((kw: string) => (
                      <Tag key={kw} color="green">{kw}</Tag>
                    ))}
                    {!sub.platform_id && !sub.keywords.length && (
                      <Tag>全部</Tag>
                    )}
                  </Space>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    创建于 {new Date(sub.created_at).toLocaleString("zh-CN")}
                  </Text>
                </div>
                <Popconfirm title="确认取消此订阅？" onConfirm={() => deleteSub(sub.id)}>
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </div>
            </Card>
          )}
        />
      )}
    </div>
  );
}
