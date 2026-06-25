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

export function useSearchArticles(q: string, platforms?: string, page = 1) {
  return useQuery({
    queryKey: ["articles", "search", q, platforms, page],
    queryFn: () => searchArticles(q, platforms, page),
    staleTime: 120_000,
    enabled: q.length > 0,
  });
}
