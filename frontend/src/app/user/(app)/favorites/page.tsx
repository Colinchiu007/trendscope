"use client";

import { useState, useEffect } from "react";
import { Card, List, Button, Space, Tag, Spin, Empty, Typography, message } from "antd";
import { DeleteOutlined, EyeOutlined, HeartFilled, LinkOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";

const { Text } = Typography;

interface FavoriteItem {
  id: number;
  article_id: number;
  article: {
    title: string;
    platform_code: string;
    platform_name: string;
    source_url: string;
    summary: string;
    like_count: number;
    read_count: number;
  } | null;
  created_at: string;
}

export default function FavoritesPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<FavoriteItem[]>([]);

  const fetchFavorites = async () => {
    setLoading(true);
    try {
      const res: any = await apiClient.get("/user/favorites");
      if (res.code === 0) setItems(res.data.items);
    } catch {
      message.error("加载收藏失败");
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchFavorites(); }, []);

  const removeFavorite = async (id: number) => {
    try {
      const res: any = await apiClient.delete(`/user/favorites/${id}`);
      if (res.code === 0) {
        message.success("已取消收藏");
        setItems((prev) => prev.filter((i) => i.id !== id));
      }
    } catch { message.error("取消失败"); }
  };

  if (loading) return <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div>;

  return (
    <div>
      <h3 style={{ marginBottom: 16 }}>
        <HeartFilled style={{ color: "#f5222d", marginRight: 8 }} />
        我的收藏
      </h3>

      {items.length === 0 ? (
        <Card style={{ borderRadius: 12, textAlign: "center", padding: 40 }}>
          <Empty description="还没有收藏文章" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          <Button type="primary" style={{ marginTop: 16 }} onClick={() => router.push("/")}>
            去发现热门文章
          </Button>
        </Card>
      ) : (
        <List
          dataSource={items}
          renderItem={(item) => (
            <Card hoverable style={{ marginBottom: 8, borderRadius: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {item.article ? (
                    <>
                      <Text
                        style={{ fontSize: 15, fontWeight: 500, cursor: "pointer" }}
                        onClick={() => router.push(`/article/${item.article_id}`)}
                      >
                        {item.article.title}
                      </Text>
                      <div style={{ marginTop: 4 }}>
                        <Space size={4} wrap>
                          <Tag color="blue" style={{ fontSize: 11 }}>{item.article.platform_name}</Tag>
                          {item.article.read_count > 0 && (
                            <Text type="secondary" style={{ fontSize: 11 }}>{item.article.read_count.toLocaleString()} 阅读</Text>
                          )}
                          {item.article.like_count > 0 && (
                            <Text type="secondary" style={{ fontSize: 11 }}>{item.article.like_count.toLocaleString()} 赞</Text>
                          )}
                        </Space>
                      </div>
                      <Text type="secondary" style={{ fontSize: 11, display: "block", marginTop: 4 }}>
                        收藏于 {new Date(item.created_at).toLocaleString("zh-CN")}
                      </Text>
                    </>
                  ) : (
                    <Text type="secondary">文章已被移除</Text>
                  )}
                </div>
                <Space>
                  {item.article && (
                    <>
                      <Button type="text" size="small" icon={<LinkOutlined />}
                        onClick={() => item.article?.source_url && window.open(item.article.source_url, "_blank")} />
                      <Button type="text" size="small" icon={<EyeOutlined />}
                        onClick={() => router.push(`/article/${item.article_id}`)} />
                    </>
                  )}
                  <Button type="text" size="small" danger icon={<DeleteOutlined />}
                    onClick={() => removeFavorite(item.id)} />
                </Space>
              </div>
            </Card>
          )}
        />
      )}
    </div>
  );
}
