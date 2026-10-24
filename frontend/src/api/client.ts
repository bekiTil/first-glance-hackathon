// SHARED: typed API calls. Owner: Yared. Types come from ../../openapi.json (npm run gen:api).
import type { components } from "./types";

export type Schemas = components["schemas"];
export type WatchOut = Schemas["WatchOut"];
export type Checklist = Schemas["Checklist"];
export type DecisionOut = Schemas["DecisionOut"];
export type Stats = Schemas["Stats"];
export type FreeEvent = Schemas["FreeEvent"];
export type StudyOut = Schemas["StudyOut"];
export type LandingCopy = Schemas["LandingCopy"];
export type AgentName = DecisionOut["agent"];

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = await res.text();
    try {
      detail = JSON.parse(detail).detail ?? detail;
    } catch {
      /* not JSON */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
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
  companyLog: (limit = 100, agent?: AgentName) =>
    request<DecisionOut[]>(`/api/company/log?limit=${limit}${agent ? `&agent=${agent}` : ""}`),
  stats: () => request<Stats>("/api/company/stats"),
  freeEvents: (when = "tonight") => request<FreeEvent[]>(`/api/free-events?when=${encodeURIComponent(when)}`),
  landingCopy: () => request<LandingCopy>("/api/studies/landing-copy"),
  getStudy: (id: string) => request<StudyOut>(`/api/studies/${id}`),
  submitStudy: (id: string, body: Schemas["StudyAnswerIn"]) =>
    post<Schemas["OkOut"]>(`/api/studies/${id}/answers`, body),
};
