import { request } from "./http";

export async function createTelegramLink() {
  return request<{ code: string; expires_in: number }>("/users/telegram/link", {
    method: "POST",
    auth: true,
  });
}

export async function unlinkTelegram() {
  return request<{ ok: boolean }>("/users/telegram/unlink", {
    method: "POST",
    auth: true,
  });
}