"use client";

import { Card, Typography, Space, Button, Skeleton, Tag } from "antd";
import { FireOutlined, ReloadOutlined, RightOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { usePlatformTrending } from "@/hooks/useTrending";
import { PLATFORM_COLORS, PLATFORM_LOGOS } from "@/lib/constants";
import { useEffect, useRef, useState } from "react";
import type { TrendingTopic } from "@/lib/types";

const { Text } = Typography;

interface HotListCardProps {
  platformCode: string;
  platformName: string;
}

export function HotListCard({ platformCode, platformName }: HotListCardProps) {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { data, isLoading, refetch } = usePlatformTrending(platformCode, 1);
  const [lastRefetch, setLastRefetch] = useState(0);
  const [localLoading, setLocalLoading] = useState(true);

  useEffect(() => {
    if (visible && !isLoading) {
      setLocalLoading(false);
    }
  }, [visible, isLoading]);

  // IntersectionObserver 懒加载
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); observer.unobserve(el); } },
      { rootMargin: "100px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const items: TrendingTopic[] = data?.data?.items?.slice(0, 15) || [];
  const accentColor = PLATFORM_COLORS[platformCode] || "#666";

  console.log(`[${platformCode}] visible=${visible} items=${items.length}`, data);

  // 防抖刷新（60秒间隔）
  const handleRefresh = () => {
    const now = Date.now();
    if (now - lastRefetch < 60000) { return; }
    setLastRefetch(now);
    refetch();
  };

  return (
    <div ref={ref}>
      <Card
        hoverable
        style={{ borderRadius: 12, height: "100%" }}
        styles={{ body: { padding: 0 } }}
        onClick={() => router.push(`/trending/${platformCode}`)}
      >
        {/* Header: logo + name + type */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 16px 0" }}>
          <Space>
            <img
              src={PLATFORM_LOGOS[platformCode] || "/logos/default.png"}
              alt={platformName}
              style={{ width: 20, height: 20, borderRadius: 4 }}
              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
            />
            <Text strong style={{ fontSize: 15 }}>{platformName}</Text>
          </Space>
          {!isLoading && items.length > 0 && (
            <Tag color={accentColor} style={{ fontSize: 11, borderRadius: 4 }}>{items.length}条</Tag>
          )}
        </div>

        {/* Body: top items */}
        <div style={{ padding: "8px 16px 0", minHeight: 280 }}>
          {!visible ? (
            <Skeleton active paragraph={{ rows: 8 }} />
          ) : localLoading ? (
            <Skeleton active paragraph={{ rows: 8 }} />
          ) : !items || items.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 0", color: "#bbb" }}>
              <Text type="secondary">暂无数据</Text>
            </div>
          ) : (
            items.map((item, idx) => (
              <div
                key={item.id}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "5px 0", cursor: "pointer", borderRadius: 6,
                  transition: "all 0.2s",
                }}
                className="hot-list-item"
                onClick={(e) => { e.stopPropagation(); window.open(item.topic_url, "_blank"); }}
              >
                <div
                  style={{
                    width: 22, height: 22, borderRadius: 6,
                    background: idx < 3 ? accentColor : "#f0f0f0",
                    color: idx < 3 ? "#fff" : "#999",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 11, fontWeight: 600, flexShrink: 0,
                  }}
                >
                  {idx + 1}
                </div>
                <Text
                  ellipsis
                  style={{
                    fontSize: 13, lineHeight: 1.4,
                    color: idx < 3 ? "#1a1a1a" : "#555",
                  }}
                >
                  {item.title}
                </Text>
              </div>
            ))
          )}
        </div>

        {/* Footer: refresh + more */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 16px 14px" }}>
          <Button
            type="text" size="small" icon={<ReloadOutlined />}
            onClick={(e) => { e.stopPropagation(); handleRefresh(); }}
            disabled={Date.now() - lastRefetch < 60000}
          >
            刷新
     