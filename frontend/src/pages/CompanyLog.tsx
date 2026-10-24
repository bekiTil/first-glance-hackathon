// The judges' page: live numbers, the Terac before/after, and every agent decision. Owner: Yared.
import { useEffect, useState } from "react";
import { api, type DecisionOut, type SelfTestOut, type Stats } from "../api/client";
import { Card, timeAgo } from "../ui";

const AGENT_COLORS: Record<string, string> = {
  ceo: "bg-purple-100 text-purple-800", growth: "bg-green-100 text-green-800",
  support: "bg-blue-100 text-blue-800", watcher: "bg-amber-100 text-amber-800",
  finance: "bg-emerald-100 text-emerald-800", compliance: "bg-red-100 text-red-800",
  research: "bg-sky-100 text-sky-800",
};

const pct = (v: unknown) => (typeof v === "number" ? `${Math.round(v * 100)}%` : "–");

export default function CompanyLog() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [log, setLog] = useState<DecisionOut[]>([]);
  const [self, setSelf] = useState<SelfTestOut | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = () => {
      api.stats().then(setStats).catch((e) => setError(String(e.message ?? e)));
      api.companyLog(200).then(setLog).catch((e) => setError(String(e.message ?? e)));
      api.selfTest().then(setSelf).catch(() => {});
    };
    load();
    const timer = setInterval(load, 10_000);
    return () => clearInterval(timer);
  }, []);

  const results = self?.results;

  return (
    <section className="py-8">
      <h1 className="text-3xl font-bold">Company log</h1>
      <p className="mt-1 text-slate-600">FirstGlance is run by AI agents. Everything they decide shows up here, live.</p>
      {error && <p className="mt-2 text-sm text-amber-700">Some data isn't available yet: {error}</p>}

      {stats && (
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {([
            ["Revenue", `$${stats.revenue_usd.toFixed(2)}`],
            ["Tests paid", stats.tests_paid],
            ["Reports delivered", stats.tests_delivered],
            ["Our rewrite won", `${Math.round(stats.rewrite_win_rate * 100)}%`],
          ] as const).map(([label, value]) => (
            <Card key={label}>
              <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
              <p className="mt-1 text-3xl font-bold">{value}</p>
            </Card>
          ))}
        </div>
      )}

      {self && (
        <div className="mt-6 rounded-xl border-2 border-sky-300 bg-sky-50 p-5">
          <p className="font-bold">We test our own landing page with real people (via Terac)</p>
          {results ? (
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div>
                <p className="text-sm text-slate-600">Understood what we do in 10 seconds</p>
                <p className="text-2xl font-bold">{pct(results.original.understood_rate)} → {pct(results.rewrite.understood_rate)}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Would sign up (1-5)</p>
                <p className="text-2xl font-bold">{results.original.avg_signup} → {results.rewrite.avg_signup}</p>
              </div>
              <p className="text-sm sm:col-span-2">{results.summary}</p>
            </div>
          ) : (
            <p className="mt-2 text-sm">Test status: {self.status ?? "starting"}. Real people are looking at it now.</p>
          )}
        </div>
      )}

      <ul className="mt-6 space-y-2">
        {log.map((d) => (
          <li key={d.id} className="rounded-lg border border-slate-200 p-3 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span>
                <span className={`mr-2 rounded px-2 py-0.5 font-mono text-xs ${AGENT_COLORS[d.agent] ?? "bg-slate-100"}`}>
                  {d.agent}
                </span>
                <b>{d.action.replaceAll("_", " ")}</b>
              </span>
              <span className="shrink-0 text-xs text-slate-400">{timeAgo(d.created_at)}</span>
            </div>
            <p className="mt-1 text-slate-700">{d.reason}</p>
          </li>
        ))}
        {log.length === 0 && !error && <li className="text-slate-500">No decisions yet.</li>}
      </ul>
    </section>
  );
}
