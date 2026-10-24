// Terac participants land here (task_url). Answers go to our DB; then they return to Terac. Owner: Yared.
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { api, type StudyOut } from "../api/client";
import { Button, Card, ErrorText, inputClass } from "../ui";

export default function Study() {
  const { id = "" } = useParams();
  const [params] = useSearchParams();
  const participant = params.get("teracSubmissionId") ?? params.get("submissionId") ?? undefined;
  const [study, setStudy] = useState<StudyOut | null>(null);
  const [picks, setPicks] = useState<Record<number, string>>({});
  const [why, setWhy] = useState<Record<number, string>>({});
  const [willingness, setWillingness] = useState(0);
  const [unclear, setUnclear] = useState("");
  const [done, setDone] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.getStudy(id).then(setStudy).catch((e) => setError(String(e.message ?? e)));
  }, [id]);

  if (done) {
    return (
      <section className="py-16 text-center">
        <p className="text-2xl font-bold">✅ {done}</p>
        <p className="mt-2 text-slate-600">You can close this tab now.</p>
      </section>
    );
  }
  if (!study) return <section className="py-8"><ErrorText error={error} />{!error && "Loading…"}</section>;

  const complete = study.sets.every((_, i) => picks[i]) && willingness > 0;

  async function submit() {
    setError("");
    try {
      const res = await api.submitStudy(id, {
        participant_ref: participant,
        picks: study!.sets.map((_, i) => ({ set: i, option: picks[i], why: why[i] ?? "" })),
        willingness,
        unclear,
      });
      setDone(res.message ?? "Thank you!");
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  }

  return (
    <section className="space-y-6 py-6">
      <div>
        <h1 className="text-2xl font-bold">Which tickets would you buy?</h1>
        <p className="mt-1 text-slate-600">
          5 quick picks + 2 questions, about 5 minutes. Imagine you're buying 2 tickets for yourself. Prices are
          per ticket, including fees. There are no right answers.
        </p>
      </div>

      {study.sets.map((set, i) => (
        <Card key={set.event}>
          <p className="font-semibold">{i + 1}. {set.event}</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {set.options.map((o) => (
              <button key={o.label} type="button" onClick={() => setPicks({ ...picks, [i]: o.label })}
                className={`rounded-lg border p-3 text-left transition ${
                  picks[i] === o.label ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 hover:bg-slate-50"
                }`}>
                <p className="text-xl font-bold">${o.price}</p>
                <p className="text-sm">{o.section}</p>
                <p className="text-sm opacity-80">{o.day}</p>
              </button>
            ))}
          </div>
          <input value={why[i] ?? ""} onChange={(e) => setWhy({ ...why, [i]: e.target.value })}
            placeholder="Why that one? (optional)" className={`${inputClass} mt-3 text-sm`} />
        </Card>
      ))}

      <Card>
        <p className="font-semibold">6. Here's a new service. How likely would you be to pay ${study.price_usd} for it?</p>
        <div className="mt-3 rounded-lg bg-slate-50 p-4">
          <p className="text-lg font-bold">{study.landing.headline}</p>
          <p className="mt-1 text-slate-600">{study.landing.subhead}</p>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
            {(study.landing.bullets ?? []).map((b) => <li key={b}>{b}</li>)}
          </ul>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} type="button" onClick={() => setWillingness(n)}
              className={`h-12 w-12 rounded-lg border text-lg font-bold ${
                willingness === n ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300"
              }`}>
              {n}
            </button>
          ))}
          <span className="self-center text-sm text-slate-500">1 = not at all · 5 = very likely</span>
        </div>
      </Card>

      <Card>
        <p className="font-semibold">7. What's unclear or missing about this service?</p>
        <textarea value={unclear} onChange={(e) => setUnclear(e.target.value)} rows={3}
          placeholder="Anything that would stop you from paying" className={`${inputClass} mt-3`} />
      </Card>

      <ErrorText error={error} />
      <Button disabled={!complete} onClick={submit}>Submit answers</Button>
      {!complete && <p className="text-sm text-slate-500">Pick one ticket in every set and choose 1-5 to submit.</p>}
    </section>
  );
}
