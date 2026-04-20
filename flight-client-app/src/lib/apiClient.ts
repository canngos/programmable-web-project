import axios from "axios";
import { API_BASE_URL } from "../config";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

type ApiErrorBody = {
  message?: string;
  error?: string;
  /** Marshmallow validation: field name -> list of messages */
  errors?: Record<string, string[] | string | Record<string, unknown>>;
};

function flattenValidationMessages(errors: ApiErrorBody["errors"]): string[] {
  if (!errors || typeof errors !== "object") return [];
  const out: string[] = [];
  for (const msgs of Object.values(errors)) {
    if (Array.isArray(msgs)) {
      out.push(...msgs.map(String));
    } else if (typeof msgs === "string") {
      out.push(msgs);
    } else if (msgs && typeof msgs === "object") {
      out.push(...flattenValidationMessages(msgs as Record<string, string[] | string>));
    }
  }
  return out;
}

export const getApiErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiErrorBody | undefined;
    const fieldMessages = flattenValidationMessages(data?.errors);
    if (fieldMessages.length > 0) {
      return fieldMessages.join(" ");
    }
    return data?.message ?? data?.error ?? error.message;
  }
  return "Unexpected error occurred.";
};

