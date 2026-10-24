// Order a test: URL + one sentence -> preview original vs. our rewrite -> pay on Whop. Owner: Yared.
import { useState } from "react";
import { api, type HeroCopy, type TestOut } from "../api/client";
import { Button, Card, ErrorText, inputClass } from "../ui";

function Hero({ label, copy }: { label: string; copy?: HeroCopy | null }) {
  return (
    <Card>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      {copy ? (
        <>
          <p className="mt-2 text-xl font-bold">{copy.headline}</p>
          {copy.subhead && <p className="mt-1 text-slate-600">{copy.subhead}</p>}
          {copy.cta && <span className="mt-3 inline-block rounded bg-slate-900 px-3 py-1.5 text-sm text-white">{copy.cta}</span>}
        </>
      ) : (
        <p className="mt-2 text-slate-400">–</p>
      )}
    </Card>
  );
}

export default function NewTest() {
  const [url, setUrl] = useState("");
  const [whatYouDo, setWhatYouDo] = useState("");
  const [email, setEmail] = useState("");
  const [test, setTest] = useState<TestOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      const msg = String((e as Error).message ?? e);
      setError(msg.includes("read") ? "We couldn't read that page. Is it public? Try the full https:// address." : msg);
    } finally {
      setBusy(false);
    }
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const normalized = /^https?:\/\//.test(url) ? url : `https://${url}`;
    run(async () => setTest(await api.createTest({ url: normalized, what_you_do: whatYouDo, email })));
  };

  const pay = () =>
    run(async () => {
      const { checkout_url } = await api.confirmTest(test!.id);
      window.location.href = checkout_url;
    });

  if (test) {
    return (
      <section className="space-y-5 py-8">
        <h1 className="text-2xl font-bold">Here's what we'll test</h1>
        <div className="grid gap-3 sm:grid-cols-2">
          <Hero label="Yours (what visitors see now)" copy={test.original} />
          <Hero label="Our rewrite" copy={test.rewrite} />
        </div>
        <Card>
          <p className="font-semibold">What happens next</p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-600">
            <li>About 10 real people each see one version for 5 seconds.</li>
            <li>They tell us what they think you do and whether they'd sign up.</li>
            <li>You get a report by email with the winner and the copy to paste in, usually within a couple of hours.</li>
            <li>If our version doesn't beat yours, you're refunded automatically.</li>
          </ol>
        </Card>
        <ErrorText error={error} />
        <Button disabled={busy} onClick={pay}>Test both for ${test.price_usd}</Button>
      </section>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-4 py-8">
      <h1 className="text-2xl font-bold">Test my landing page</h1>
      <label className="block">
        <span className="font-semibold">Landing page URL</span>
        <input required value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://yourstartup.com"
          className={`${inputClass} mt-1`} />
      </label>
      <label className="block">
        <span className="font-semibold">In one sentence: what do you do, and for whom?</span>
        <input required minLength={5} value={whatYouDo} onChange={(e) => setWhatYouDo(e.target.value)}
          placeholder="Payroll software for small dental clinics" className={`${inputClass} mt-1`} />
        <span className="text-sm text-slate-500">We use this to check whether people understood you.</span>
      </label>
      <label className="block">
        <span className="font-semibold">Email for your report</span>
        <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={`${inputClass} mt-1`} />
      </label>
      <ErrorText error={error} />
      <Button type="submit" disabled={busy}>{busy ? "Reading your page and writing a rewrite…" : "Next"}</Button>
    </form>
  );
}
