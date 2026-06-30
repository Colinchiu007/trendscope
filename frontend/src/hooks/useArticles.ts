"use client";

import { useQuery, useInfiniteQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { ApiResponse, ArticleListData, HotArticle } from "@/lib/types";

async function fetchArticles(
  platforms?: string,
  timeRange = "24h",
  page = 1,
  pageSize = 20
): Promise<ApiResponse<ArticleListData>> {
  const params: Record<string, string | number> = { page, page_size: pageSize, time_range: timeRange };
  if (platforms) params.platforms = platforms;
  return apiClient.get("/articles", { params });
}

async function fetchArticle(id: number): Promise<ApiResponse<HotArticle>> {
  return apiClient.get(`/articles/${id}`);
}

async function searchArticles(
  q: string,
  platforms?: string,
  page = 1,
  pageSize = 20
): Promise<ApiResponse<ArticleListData>> {
  const params: Record<string, string | number> = { q, page, page_size: pageSize };
  if (platforms) params.platforms = platforms;
  return apiClient.get("/articles/search", { params });
}

async function fetchRelatedArticles(articleId: number):
  Promise<ApiResponse<{ items: HotArticle[] }>> {
  return apiClient.get(`/articles/${articleId}/related`, { params: { limit: 5 } });
}

export function useArticles(platforms?: string, timeRange = "24h", page = 1) {
  return useQuery({
    queryKey: ["articles", platforms, timeRange, page],
    queryFn: () => fetchArticles(platforms, timeRange, page),
    staleTime: 60_000,
  });
}

export function useArticle(id: number) {
  return useQuery({
    queryKey: ["article", id],
    queryFn: () => fetchArticle(id),
    staleTime: 300_000,
    enabled: id > 0,
  });
}

export function useRelatedArticles(articleId: number) {
  return useQuery({
    queryKey: ["articles", "related", articleId],
    queryFn: () => fetchRelatedArticles(articleId),
    staleTime: 300_000,
    enabled: articleId > 0,
  });
}

export function useSearchArticles(q: string, platforms?: string, page = 1) {
  return useQuery({
    queryKey: ["articles", "search", q, platforms, page],
    queryFn: () => searchArticles(q, platforms, page),
    staleTime: 120_000,
    enabled: q.length > 0,
  });
}

// ── last30days 多源搜索 ────────────────────────────────────────────

interface Last30daysResult {
  item_id: string;
  source: string;
  source_label: string;
  title: string;
  body: string;
  url: string;
  author: string;
  published_at: string | null;
  engagement: Record<string, number>;
  engagement_score: number;
  container: string;
  thumbnail: string | null;
}

interface Last30daysResponse {
  code: number;
  data: {
    query: string;
    sources: string[];
    total: number;
    results: Last30daysResult[];
    by_source: Record<string, Last30daysResult[]>;
    errors: Record<string, string>;
  };
}

async function searchLast30days(
  q: string,
  sources?: string,
  perSource = 12,
  totalMax = 30
): Promise<Last30daysResponse> {
  const params: Record<string, string | number> = { q, per_source: perSource, total_max: totalMax };
  if (sources) params.sources = sources;
  return apiClient.get("/search/last30days", { params });
}

export function useLast30daysSearch(q: string, sources?: string) {
  return useQuery({
    queryKey: ["last30days", "search", q, sources],
    queryFn: () => searchLast30days(q, sources),
    staleTime: 120_000,
    enabled: q.length > 0,
  });
}
