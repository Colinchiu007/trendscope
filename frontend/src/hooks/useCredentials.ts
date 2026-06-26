/** 平台凭证管理 Hook */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { getToken } from "@/lib/auth";

export interface CredentialField {
  key: string;
  label: string;
  env_var: string;
  type: string;
}

export interface PlatformCredentials {
  code: string;
  name: string;
  masked: Record<string, string>;
}

/** 获取所有平台的凭证字段定义 */
async function fetchCredentialFields() {
  return apiClient.get<{ code: number; data: Record<string, CredentialField[]> }>(
    "/admin/platforms/credential-fields"
  );
}

/** 获取指定平台的凭证（掩码） */
async function fetchPlatformCredentials(code: string) {
  return apiClient.get<{ code: number; data: PlatformCredentials }>(
    `/admin/platforms/${code}/credentials`
  );
}

/** 更新指定平台的凭证 */
async function updatePlatformCredentials({ code, config }: { code: string; config: Record<string, string> }) {
  return apiClient.put<{ code: number; message: string }>(
    `/admin/platforms/${code}/credentials`,
    { config }
  );
}

/** Hook: 凭证字段定义 */
export function useCredentialFields() {
  return useQuery({
    queryKey: ["credentials", "fields"],
    queryFn: fetchCredentialFields,
    enabled: !!getToken(),
    staleTime: 300_000,
  });
}

/** Hook: 单个平台凭证 */
export function usePlatformCredentials(code: string) {
  return useQuery({
    queryKey: ["credentials", code],
    queryFn: () => fetchPlatformCredentials(code),
    enabled: !!getToken() && !!code,
    staleTime: 30_000,
  });
}

/** Hook: 更新凭证 mutation */
export function useSaveCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updatePlatformCredentials,
    onSuccess: (_data, variables) => {
      // 刷新该平台的凭证缓存
      queryClient.invalidateQueries({ queryKey: ["credentials", variables.code] });
    },
  });
}
