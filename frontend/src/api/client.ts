// SHARED: typed API calls. Owner: Yared. Types come from ../../openapi.json (npm run gen:api).
import type { components } from "./types";

export type Schemas = components["schemas"];
export type WatchOut = Schemas["WatchOut"];
export type Checklist = Schemas["Checklist"];
export type DecisionOut = Schemas["DecisionOut"];
export type Stats = Schemas["Stats"];
export type FreeEvent = Schemas["FreeEvent"];

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  createWatch: (body: Schemas["CreateWatchRequest"]) => post<WatchOut>("/api/watches", body),
  getWatch: (id: string) => request<WatchOut>(`/api/watches/${id}`),
  updateChecklist: (id: string, checklist: Checklist) =>
    request<WatchOut>(`/api/watches/${id}`, { method: "PATCH", body: JSON.stringify({ checklist }) }),
  confirmWatch: (id: string) => post<Schemas["CheckoutOut"]>(`/api/watches/${id}/confirm`),
  sendCode: (watch_id: string, phone: string) => post<Schemas["OkOut"]>("/api/phone/send-code", { watch_id, phone }),
  verifyCode: (phone: string, code: string) => post<Schemas["VerifyOut"]>("/api/phone/verify", { phone, code }),
  login: (email: string) => post<Schemas["OkOut"]>("/api/me/login", { email }),
  myWatches: (token: string) => request<WatchOut[]>(`/api/me/watches?token=${encodeURIComponent(token)}`),
  companyLog: (limit = 100) => request<DecisionOut[]>(`/api/company/log?limit=${limit}`),
  stats: () => request<Stats>("/api/company/stats"),
  freeEvents: (when = "tonight") => request<FreeEvent[]>(`/api/free-events?when=${encodeURIComponent(when)}`),
};
