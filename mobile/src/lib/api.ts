import axios, { AxiosError, AxiosInstance } from 'axios';

const DEFAULT_API_URL = 'http://127.0.0.1:5000';

function resolveApiBaseUrl(): string {
  const configured = process.env.EXPO_PUBLIC_API_URL?.trim();
  return configured || DEFAULT_API_URL;
}

export const apiBaseUrl = resolveApiBaseUrl();

export const apiClient: AxiosInstance = axios.create({
  baseURL: apiBaseUrl,
  timeout: 120000,
});

export const visionToolsEnabled =
  process.env.EXPO_PUBLIC_ENABLE_VISION_TOOLS === '1' ||
  process.env.EXPO_PUBLIC_ENABLE_VISION_TOOLS === 'true';

type ApiErrorBody = {
  detail?: string | { msg?: string };
  message?: string;
  error?: string;
};

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorBody>;
    const data = axiosError.response?.data;
    if (typeof data?.detail === 'string' && data.detail.trim()) {
      return data.detail;
    }
    if (typeof data?.message === 'string' && data.message.trim()) {
      return data.message;
    }
    if (typeof data?.error === 'string' && data.error.trim()) {
      return data.error;
    }
    if (axiosError.message?.trim()) {
      return axiosError.message;
    }
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
}
