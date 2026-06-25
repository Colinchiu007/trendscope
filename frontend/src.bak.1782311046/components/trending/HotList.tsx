"use client";

import { Spin, Empty, Pagination } from "antd";
import { LoadingOutlined } from "@ant-design/icons";
import { TrendingCard } from "./TrendingCard";
import type { TrendingTopic } from "@/lib/types";

interface HotListProps {
  items: TrendingTopic[];
  loading: boolean;
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function HotList({
  items,
  loading,
  page,
  pageSize,
  total,
  onPageChange,
}: HotListProps) {
  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "60px 0" }}>
        <Spin indicator={<LoadingOutlined spin />} size="large" />
        <p style={{ marginTop: 16, color: "#999" }}>正在加载热榜数据...</p>
      </div>
    );
  }

  if (!items.length) {
    return (
      <Empty
        description="暂无热榜数据"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        style={{ padding: "60px 0" }}
      />
    );
  }

  return (
    <div>
      {items.map((item) => (
        <TrendingCard key={item.id} item={item} />
      ))}
      {total > pageSize && (
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <Pagination
            current={page}
            pageSize={pageSize}
            total={total}
            onChange={onPageChange}
            showSizeChanger={false}
            size="small"
          />
        </div>
      )}
    </div>
  );
}
