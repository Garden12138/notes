import axios from "axios";

import type { ArchitectureSnapshot } from "../types/architecture";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api",
  timeout: 120_000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getApiErrorMessage(
  reason: unknown,
  fallback = "请求失败，请稍后重试",
): string {
  if (axios.isAxiosError(reason)) {
    const detail = reason.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => (typeof item?.msg === "string" ? item.msg : ""))
        .filter(Boolean);
      if (messages.length) {
        return messages.join("；");
      }
    }
    if (reason.code === "ECONNABORTED") {
      return "规划请求超时，请稍后重试";
    }
    return reason.message || fallback;
  }
  return reason instanceof Error ? reason.message : fallback;
}

export async function fetchArchitecture(): Promise<ArchitectureSnapshot> {
  const response = await api.get<ArchitectureSnapshot>("/system/architecture");
  return response.data;
}
