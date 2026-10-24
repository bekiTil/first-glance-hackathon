// Landing page. The hero copy comes from /api/landing-copy, so the Research agent's winning
// version (tested with real people) goes live by itself. Owner: Yared.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type DecisionOut, type HeroCopy } from "../api/client";
import { Card, timeAgo } from "../ui";

const FALLBACK: HeroCopy = {
  headline: "Do people get your startup in 5 seconds?",
  subhead: "Real people see your landing page for 5 seconds. AI rewrites what confused them, and you get proof the new version works.",
  cta: "Test my page for $15",
};

export default function Landing() {
  const [copy, setCopy] = useState<HeroCopy>(FALLBACK);
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
        <Link to="/test/new"
          className="mt-8 inline-block rounded-lg bg-slate-900 px-6 py-3 font-semibold text-white hover:bg-slate-700">
          {copy.cta || "Test my page"}
        </Link>
        <p className="mt-3 text-sm text-slate-500">Refunded automatically if our version doesn't beat yours. Run entirely by AI agents.</p>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {[
          ["1. Paste your URL", "Plus one sentence: what you do and for whom."],
          ["2. Real people, 5 seconds", "About 10 people see yours or our rewrite, then say what they think you do."],
          ["3. Proof", "“3/5 understood yours, 5/5 understood ours.” Plus the copy to paste in."],
        ].map(([title, body]) => (
          <Card key={title}>
            <p className="font-semibold">{title}</p>
            <p className="mt-1 text-sm text-slate-600">{body}</p>
          </Card>
        ))}
      </section>

      {picks.length > 0 && (
        <section className="mt-10">
          <h2 className="text-xl font-bold">From our Growth agent</h2>
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
      </p>
    </>
  );
}
