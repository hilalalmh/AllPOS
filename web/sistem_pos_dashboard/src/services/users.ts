import { apiClient } from "./api";
import type { UserList, UserMe } from "../types";

export interface UserQuery {
  q?: string;
  page?: number;
  page_size?: number;
}

export interface UserCreateInput {
  username: string;
  password: string;
  full_name: string;
  role: "OWNER" | "KASIR";
}

export interface UserUpdateInput {
  full_name?: string;
  role?: "OWNER" | "KASIR";
  is_active?: boolean;
  password?: string;
}

export async function fetchUsers(params: UserQuery): Promise<UserList> {
  const { data } = await apiClient.get<UserList>("/users", { params });
  return data;
}

export async function createUser(
  payload: UserCreateInput
): Promise<UserMe> {
  const { data } = await apiClient.post<UserMe>("/users", payload);
  return data;
}

export async function updateUser(
  id: number,
  payload: UserUpdateInput
): Promise<UserMe> {
  const { data } = await apiClient.put<UserMe>(`/users/${id}`, payload);
  return data;
}

export async function changeOwnPassword(
  currentPassword: string,
  newPassword: string
): Promise<void> {
  await apiClient.put("/users/me/password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}