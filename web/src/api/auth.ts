import { request, tokenStorage } from "./http";

export type TokenPair = { access_token: string; refresh_token: string; token_type: string };

export async function register(email: string, password: string) {
  return request<{ id: number; email: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export async function login(email: string, password: string) {
  const res = await request<TokenPair>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  tokenStorage.writeTokens(res.access_token, res.refresh_token);
  return res;
}

export async function logout(refresh_token: string) {
  await request("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token }) });
  tokenStorage.clearTokens();
}
