"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type {
  ApiResponse, TrendingListData, Platform, PlatformSummaryItem, TrendHistoryData,
} from "@/lib/types";

async function fetchAggregatedTrending(
  platforms?: string, page = 1
): Promise<ApiResponse<TrendingListData>> {
  const params: Record<string, string | number> = { page, page_size: 30 };
  if (platforms) params.platforms = platforms;
  return apiClient.get("/trending", { params });
}

async function fetchPlatformTrending(platform: string, page = 1):
  Promise<ApiResponse<TrendingListData>> {
  return apiClient.get(`/trending/${platform}`, {
    params: { page, page_size: 50 },
  });
}

async function fetchPlatforms(): Promise<ApiResponse<{ platforms: Platform[] }>> {
  return apiClient.get("/trending/platforms");
}

async function fetchPlatformSummary():
  Promise<ApiResponse<{ platforms: PlatformSummaryItem[] }>> {
  return apiClient.get("/trending/summary");
}

async function fetchTrendingHistory(
  topicId: number, range = "7d"
): Promise<ApiResponse<TrendHistoryData>> {
  return apiClient.get("/trending/history", {
    params: { topic_id: topicId, range },
  });
}

export function useAggregatedTrending(platforms?: string, page = 1) {
  return useQuery({
    queryKey: ["trending", "aggregated", platforms, page],
    queryFn: () => fetchAggregatedTrending(platforms, page),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}

export function usePlatformTrending(platform: string, page = 1) {
  return useQuery({
    queryKey: ["trending", platform, page],
    queryFn: () => fetchPlatformTrending(platform, page),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export function usePlatforms() {
  return useQuery({
    queryKey: ["platforms"],
    queryFn: fetchPlatforms,
    staleTime: 600_000,
  });
}

export function usePlatformSummary() {
  return useQuery({
    queryKey: ["platform-summary"],
    queryFn: fetchPlatformSummary,
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}

export function useTrendingHistory(topicId: number, enabled = false, range = "7d") {
  return useQuery({
    queryKey: ["trending", "history", topicId, range],
    queryFn: () => fetchTrendingHistory(topicId, range),
    staleTime: 300_000,
    enabled: topicId > 0 && enabled,
  });
}
