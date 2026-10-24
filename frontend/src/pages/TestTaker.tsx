// Terac participants land here (task_url): see ONE version for 5 seconds, then 2 questions. Owner: Yared.
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { api, type TestPageOut } from "../api/client";
import { Button, ErrorText, inputClass } from "../ui";

type Step = "intro" | "showing" | "questions" | "done";

export default function TestTaker() {
  const { id = "" } = useParams();
  const [params] = useSearchParams();
  const participant = params.get("teracSubmissionId") ?? params.get("submissionId") ?? undefined;
  const [page, setPage] = useState<TestPageOut | null>(null);
  const [step, setStep] = useState<Step>("intro");
  const [left, setLeft] = useState(5);
  const [answer, setAnswer] = useState("");
  const [signup, setSignup] = useState(0);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.getTestPage(id, participant).then(setPage).catch((e) => setError(String(e.message ?? e)));
  }, [id, participant]);

  useEffect(() => {
    if (step !== "showing" || !page) return;
    setLeft(page.seconds ?? 5);
    const tick = setInterval(() => setLeft((s) => s - 1), 1000);
    const end = setTimeout(() => setStep("questions"), (page.seconds ?? 5) * 1000);
    return () => {
      clearInterval(tick);
      clearTimeout(end);
    };
  }, [step, page]);

  async function submit() {
    setError("");
    try {
      const res = await api.submitAnswer(id, { participant_ref: participant, arm: page!.arm, answer, signup });
      setMessage(res.message ?? "Thanks!");
      setStep("done");
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  }

  if (!page) {
    return <section className="py-16 text-center"><ErrorText error={error} />{!error && "Loading…"}</section>;
  }

  if (step === "showing") {
    return (
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white px-6 text-center">
        <p className="absolute right-6 top-6 rounded-full bg-slate-100 px-3 py-1 font-mono text-sm">{Math.max(left, 0)}s</p>
        <h1 className="max-w-3xl text-4xl font-bold leading-tight sm:text-5xl">{page.hero.headline}</h1>
        {page.hero.subhead && <p className="mt-5 max-w-2xl text-lg text-slate-600 sm:text-xl">{page.hero.subhead}</p>}
        {page.hero.cta && (
          <span className="mt-8 rounded-lg bg-slate-900 px-6 py-3 font-semibold text-white">{page.hero.cta}</span>
        )}
      </div>
    );
  }

  if (step === "done") {
    return (
      <section className="py-16 text-center">
        <p className="text-2xl font-bold">✅ {message}</p>
        <p className="mt-2 text-slate-600">You can close this tab now.</p>
      </section>
    );
  }

  if (step === "questions") {
    return (
      <section className="mx-auto max-w-xl space-y-6 py-10">
        <label className="block">
          <span className="text-lg font-semibold">1. In your own words, what does this company do?</span>
          <textarea autoFocus rows={3} value={answer} onChange={(e) => setAnswer(e.target.value)}
            placeholder="It's a… for…" className={`${inputClass} mt-2`} />
          <span className="text-sm text-slate-500">A guess is fine. "No idea" is a useful answer too.</span>
        </label>
        <div>
          <p className="text-lg font-semibold">2. If you needed something like this, how likely would you be to sign up?</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {[1, 2, 3, 4, 5].map((n) => (
              <button key={n} type="button" onClick={() => setSignup(n)}
                className={`h-12 w-12 rounded-lg border text-lg font-bold ${
                  signup === n ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300"
                }`}>
                {n}
              </button>
            ))}
            <span className="text-sm text-slate-500">1 = not at all · 5 = very likely</span>
          </div>
        </div>
        <ErrorText error={error} />
        <Button disabled={!answer.trim() || !signup} onClick={submit}>Submit</Button>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-xl space-y-4 py-16 text-center">
      <h1 className="text-3xl font-bold">First impressions test</h1>
      <p className="text-lg text-slate-600">
        You'll see the top of a website for <b>{page.seconds} seconds</b>. Then we'll ask 2 quick questions about it.
        There are no wrong answers.
      </p>
      <Button onClick={() => setStep("showing")}>I'm ready, show me</Button>
    </section>
  );
}
