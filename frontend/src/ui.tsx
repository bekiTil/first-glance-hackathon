// Small shared UI pieces for the pages. Owner: Yared.
import type { ReactNode } from "react";

export function Button({ children, disabled, onClick, type = "button", variant = "primary" }: {
  children: ReactNode; disabled?: boolean; onClick?: () => void; type?: "button" | "submit";
  variant?: "primary" | "ghost";
}) {
  const style = variant === "primary"
    ? "bg-ink text-cream hover:bg-brand-dark disabled:bg-ink/40"
    : "border-2 border-ink text-ink hover:bg-paper";
  return (
    <button type={type} disabled={disabled} onClick={onClick}
      className={`rounded-full px-6 py-3 font-semibold transition ${style}`}>
      {children}
    </button>
  );
}

export const inputClass = "w-full rounded-xl border border-line bg-paper p-3 focus:border-ink focus:outline-none";

export function ErrorText({ error }: { error: string }) {
  return error ? <p className="text-sm text-red-600">{error}</p> : null;
}

export function Card({ children }: { children: ReactNode }) {
  return <div className="rounded-2xl border border-line bg-paper p-5">{children}</div>;
}

export function timeAgo(iso: string): string {
  const seconds = Math.max(0, (Date.now() - new Date(iso + "Z").getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}
