// SHARED: typed API calls. Owner: Yared. Types come from ../../openapi.json (npm run gen:api).
import type { components } from "./types";

export type Schemas = components["schemas"];
export type TestOut = Schemas["TestOut"];
export type HeroCopy = Schemas["HeroCopy"];
export type TestPageOut = Schemas["TestPageOut"];
export type TestResults = Schemas["TestResults"];
export type DecisionOut = Schemas["DecisionOut"];
export type Stats = Schemas["Stats"];
export type SelfTestOut = Schemas["SelfTestOut"];
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
  // ordering + report (Bereket's routes)
  createTest: (body: Schemas["CreateTestRequest"]) => post<TestOut>("/api/tests", body),
  getTest: (id: string) => request<TestOut>(`/api/tests/${id}`),
  confirmTest: (id: string) => post<Schemas["CheckoutOut"]>(`/api/tests/${id}/confirm`),
  // the page Terac participants see (Yared's routes)
  getTestPage: (id: string, participant?: string) =>
    request<TestPageOut>(`/api/t/${id}${participant ? `?participant=${encodeURIComponent(participant)}` : ""}`),
  submitAnswer: (id: string, body: Schemas["TestAnswerIn"]) => post<Schemas["OkOut"]>(`/api/t/${id}/answers`, body),
  landingCopy: () => request<HeroCopy>("/api/landing-copy"),
  selfTest: () => request<SelfTestOut>("/api/self-test"),
  // support (Natnael's route)
  contact: (body: Schemas["SupportRequest"]) => post<Schemas["OkOut"]>("/api/support", body),
  // company log (Bereket's routes)
  companyLog: (limit = 100, agent?: AgentName) =>
    request<DecisionOut[]>(`/api/company/log?limit=${limit}${agent ? `&agent=${agent}` : ""}`),
  stats: () => request<Stats>("/api/company/stats"),
};
