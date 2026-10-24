// Landing page. The copy comes from the Research agent (rewritten from Terac feedback). Owner: Yared.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type DecisionOut, type LandingCopy } from "../api/client";
import { Card, timeAgo } from "../ui";

const FALLBACK: LandingCopy = {
  headline: "Tell us your max price. We'll text you when tickets drop under it.",
  subhead: "An AI agent checks SeatGeek and Ticketmaster every 15 minutes for Knicks, Broadway and concerts.",
  bullets: ["$3 per watch", "Refunded automatically if we never find a match", "Run entirely by AI agents"],
  version: 1,
};

export default function Landing() {
  const [copy, setCopy] = useState<LandingCopy>(FALLBACK);
  const [picks, setPicks] = useState<DecisionOut[]>([]);

  useEffect(() => {
    api.landingCopy().then(setCopy).catch(() => {});
    api.companyLog(30, "growth")
      .then((log) => setPicks(log.filter((d) => d.action === "published_post").slice(0, 3)))
      .catch(() => {});
  }, []);

  return (
    <>
      <section className="py-14">
        <h1 className="text-4xl font-bold leading-tight sm:text-5xl">{copy.headline}</h1>
        <p className="mt-4 max-w-2xl text-lg text-slate-600">{copy.subhead}</p>
        <ul className="mt-6 flex flex-wrap gap-2">
          {(copy.bullets ?? []).map((b) => (
            <li key={b} className="rounded-full bg-slate-100 px-3 py-1 text-sm">✓ {b}</li>
          ))}
        </ul>
        <Link to="/watch/new"
          className="mt-8 inline-block rounded-lg bg-slate-900 px-6 py-3 font-semibold text-white hover:bg-slate-700">
          Start a watch
        </Link>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {[
          ["1. Tell us", "“Knicks under $80, any Friday in November, 2 seats.”"],
          ["2. Confirm + pay $3", "You check the exact checklist we'll hold ourselves to."],
          ["3. Get alerted", "Email + text the moment a verified match appears. Buy on the official site."],
        ].map(([title, body]) => (
          <Card key={title}>
            <p className="font-semibold">{title}</p>
            <p className="mt-1 text-sm text-slate-600">{body}</p>
          </Card>
        ))}
      </section>

      {picks.length > 0 && (
        <section className="mt-10">
          <h2 className="text-xl font-bold">Agent picks</h2>
          <p className="text-sm text-slate-500">Written by our Growth agent. No humans involved.</p>
          <div className="mt-3 space-y-3">
            {picks.map((p) => (
              <Card key={p.id}>
                <p className="font-semibold">{String(p.data.headline ?? "")}</p>
                <p className="mt-1 text-sm text-slate-600">{String(p.data.post ?? "")}</p>
                <p className="mt-1 text-xs text-slate-400">{timeAgo(p.created_at)}</p>
              </Card>
            ))}
          </div>
        </section>
      )}

      <p className="mt-10 text-sm text-slate-500">
        Every decision this company makes is public on the <Link to="/company" className="underline">Company log</Link>.
        Looking for something free tonight? <Link to="/events" className="underline">Free in NYC</Link>.
      </p>
    </>
  );
}
