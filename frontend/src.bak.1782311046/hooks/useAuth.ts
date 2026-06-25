"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { setTokens, removeTokens, getToken } from "@/lib/auth";

interface LoginParams {
  account: string;
  password: string;
}

interface RegisterParams {
  username: string;
  password: string;
  email?: string;
  phone?: string;
}

interface LoginResult {
  access_token: string;
  expires_in: number;
  user: { id: number; username: string; nickname?: string; role: string };
}

async function loginRequest(params: LoginParams) {
  return apiClient.post<{ code: number; data: LoginResult }>("/user/login", params);
}

async function registerRequest(params: RegisterParams) {
  return apiClient.post<{ code: number; data: { id: number; username: string } }>("/user/register", params);
}

async function fetchProfile() {
  return apiClient.get<{ code: number; data: any }>("/user/profile");
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: loginRequest,
    onSuccess: (res: any) => {
      if (res.code === 0 && res.data?.access_token) {
        setTokens(res.data.access_token, "");
        queryClient.invalidateQueries({ queryKey: ["user"] });
      }
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: registerRequest,
  });
}

export function useProfile() {
  return useQuery({
    queryKey: ["user", "profile"],
    queryFn: fetchProfile,
    enabled: !!getToken(),
    retry: false,
    staleTime: 300_000,
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return () => {
    removeTokens();
    queryClient.clear();
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };
}
