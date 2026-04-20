import { apiClient } from "../lib/apiClient";
import type { AuthResponse, User } from "../types";

type LoginPayload = {
  email: string;
  password: string;
};

type RegisterPayload = {
  firstname: string;
  lastname: string;
  email: string;
  password: string;
  role?: "admin" | "user";
};

export const login = async (payload: LoginPayload): Promise<AuthResponse> => {
  const response = await apiClient.post("/api/users/login", payload);
  return response.data as AuthResponse;
};

export const register = async (payload: RegisterPayload): Promise<AuthResponse> => {
  const response = await apiClient.post("/api/users/register", payload);
  return response.data as AuthResponse;
};

export const getMyProfile = async (): Promise<User> => {
  const response = await apiClient.get("/api/users/me");
  return response.data.user as User;
};

export const updateMyProfile = async (payload: Partial<RegisterPayload>): Promise<User> => {
  const response = await apiClient.patch("/api/users/me", payload);
  return response.data.user as User;
};

export const getAllUsers = async (): Promise<User[]> => {
  const response = await apiClient.get("/api/users/");
  const data = response.data as { users?: User[]; items?: User[]; data?: User[] };
  return data.users ?? data.items ?? data.data ?? [];
};

