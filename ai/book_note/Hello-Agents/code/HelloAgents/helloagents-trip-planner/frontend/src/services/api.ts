import axios from "axios";

import type { ArchitectureSnapshot } from "../types/architecture";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api",
  timeout: 10_000,
});

export async function fetchArchitecture(): Promise<ArchitectureSnapshot> {
  const response = await api.get<ArchitectureSnapshot>("/system/architecture");
  return response.data;
}
