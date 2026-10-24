// The founder's report: live status while people answer, then the results. Owner: Yared.
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { api, type HeroCopy, type Schemas, type TestOut } from "../api/client";
import { Button, Card, ErrorText, inputClass } from "../ui";

const STATUS: Record<string, string> = {
  draft: "Not paid yet",
  awaiting_payment: "Waiting for payment…",
  paid: "Payment received. Recruiting real people now…",
  testing: "Real people are looking at your page right now",
  delivered: "Your results are ready",
  refunded: "Results ready. Our rewrite didn't win, so you've been refunded",
  failed: "Something went wrong. You'll be refunded automatically",
};

const pct = (v: number) => `${Math.round(v * 100)}%`;

function ArmCard({ title, copy, arm, winner }: {
  title: string; copy?: HeroCopy | null; arm?: Schemas["ArmResult"]; winner: boolean;
}) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
        {winner && <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800">Winner</span>}
      </div>
      {copy && <p className="mt-2 text-lg font-bold">{copy.headline}</p>}
      {copy?.subhead && <p className="mt-1 text-sm text-slate-600">{copy.subhead}</p>}
      {arm && (
        <div className="mt-4 grid grid-cols-2 gap-2">
          <div>
            <p className="text-xs text-slate-500">Understood you</p>
            <p className="text-2xl font-bold">{arm.understood}/{arm.responses} <span className="text-base font-normal">({pct(arm.understood_rate)})</span></p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Would sign up</p>
            <p className="text-2xl font-bold">{arm.avg_signup}/5</p>
          </div>
          {(arm.sample_answers ?? []).length > 0 && (
            <ul className="col-span-2 mt-2 space-y-1 text-sm text-slate-600">
              {(arm.sample_answers ?? []).map((a, i) => <li key={i}>“{a}”</li>)}
            </ul>
          )}
        </div>
      )}
    </Card>
  );
}

export default function Report() {
  const { id = "" } = useParams();
  const [params] = useSearchParams();
  const [test, setTest] = useState<TestOut | null>(null);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [question, setQuestion] = useState("");
  const [sent, setSent] = useState("");

  useEffect(() => {
    const load = () => api.getTest(id).then(setTest).catch((e) => setError(String(e.message ?? e)));
    load();
    const timer = setInterval(load, 5_000);
    return () => clearInterval(timer);
  }, [id]);

  if (!test) return <section className="py-8"><ErrorText error={error} />{!error && "Loading…"}</section>;
  const r = test.results;
  const done = test.status === "delivered" || test.status === "refunded";

  return (
    <section className="space-y-5 py-8">
      {params.get("paid") && !done && <p className="rounded-lg bg-green-50 p-3 text-sm">Thanks! Your payment went through.</p>}
      <div>
        <p className="text-sm text-slate-500">{test.url}</p>
        <h1 className="text-2xl font-bold">{STATUS[test.status] ?? test.status}</h1>
        {!done && (test.status === "testing" || test.status === "paid") && (
          <p className="mt-1 text-slate-600">{test.responses_so_far ?? 0} people have answered so far. This page updates by itself.</p>
        )}
      </div>

      {r && <p className="rounded-xl bg-slate-900 p-4 text-lg font-semibold text-white">{r.summary}</p>}

      <div className="grid gap-3 sm:grid-cols-2">
        <ArmCard title="Yours" copy={test.original} arm={r?.original} winner={r?.winner === "original"} />
        <ArmCard title="Our rewrite" copy={test.rewrite} arm={r?.rewrite} winner={r?.winner === "rewrite"} />
      </div>

      {r?.winner === "rewrite" && test.rewrite && (
        <Card>
          <p className="font-semibold">Copy to paste into your site</p>
          <pre className="mt-2 whitespace-pre-wrap rounded bg-slate-50 p-3 text-sm">
{`Headline: ${test.rewrite.headline}\nSubhead: ${test.rewrite.subhead ?? ""}\nButton: ${test.rewrite.cta ?? ""}`}
          </pre>
        </Card>
      )}

      <Card>
        <p className="font-semibold">Questions? Our support agent answers by email.</p>
        {sent ? (
          <p className="mt-2 text-sm text-slate-600">{sent}</p>
        ) : (
          <div className="mt-2 space-y-2">
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Your email" className={inputClass} />
            <textarea rows={2} value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Your question" className={inputClass} />
            <Button variant="ghost" disabled={!email || question.length < 2}
              onClick={() => api.contact({ email, message: question, test_id: id })
                .then((res) => setSent(res.message ?? "Sent!"))
                .catch((e) => setError(String(e.message ?? e)))}>
              Send
            </Button>
          </div>
        )}
      </Card>
      <ErrorText error={error} />
    </section>
  );
}
