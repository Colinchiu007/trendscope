import { Suspense } from "react";

export default function SearchLayout({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<div style={{ padding: "80px", textAlign: "center" }}>加载中...</div>}>{children}</Suspense>;
}
