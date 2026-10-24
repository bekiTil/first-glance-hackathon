// Small shared UI pieces for the pages. Owner: Yared.
import type { ReactNode } from "react";

export function Button({ children, disabled, onClick, type = "button", variant = "primary" }: {
  children: ReactNode; disabled?: boolean; onClick?: () => void; type?: "button" | "submit";
  variant?: "primary" | "ghost";
}) {
  const style = variant === "primary"
    ? "bg-slate-900 text-white hover:bg-slate-700 disabled:bg-slate-400"
    : "border border-slate-300 text-slate-700 hover:bg-slate-50";
  return (
    <button type={type} disabled={disabled} onClick={onClick}
      className={`rounded-lg px-5 py-3 font-semibold transition ${style}`}>
      {children}
    </button>
  );
}

export const inputClass = "w-full rounded-lg border border-slate-300 p-3 focus:border-slate-900 focus:outline-none";

export function ErrorText({ error }: { error: string }) {
  return error ? <p className="text-sm text-red-600">{error}</p> : null;
}

export function Card({ children }: { children: ReactNode }) {
  return <div className="rounded-xl border border-slate-200 p-4">{children}</div>;
}

export function timeAgo(iso: string): string {
  const seconds = Math.max(0, (Date.now() - new Date(iso + "Z").getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}
