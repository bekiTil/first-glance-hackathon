// Request -> checklist -> confirm -> Whop checkout. Owner: Yared.
import { useState } from "react";
import { api, type Checklist, type WatchOut } from "../api/client";
import { Button, Card, ErrorText, inputClass } from "../ui";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function NewWatch() {
  const [query, setQuery] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [consent, setConsent] = useState(false);
  const [watch, setWatch] = useState<WatchOut | null>(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Checklist | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    run(async () => {
      const w = await api.createWatch({ query, email, phone: phone || null, sms_consent: consent && !!phone });
      setWatch(w);
      setDraft(w.checklist);
    });
  };

  const saveEdits = () =>
    run(async () => {
      const w = await api.updateChecklist(watch!.id, draft!);
      setWatch(w);
      setDraft(w.checklist);
      setEditing(false);
    });

  const confirm = () =>
    run(async () => {
      const { checkout_url } = await api.confirmWatch(watch!.id);
      window.location.href = checkout_url;
    });

  if (watch && draft) {
    const c = watch.checklist;
    return (
      <section className="space-y-5 py-8">
        <h1 className="text-2xl font-bold">I'll alert you when I find:</h1>
        {!editing ? (
          <Card>
            <ul className="space-y-1">
              <li>✅ {c.performer}{c.venue ? ` at ${c.venue}` : ""}</li>
              <li>✅ Between {c.date_from} and {c.date_to}
                {(c.weekdays ?? []).length > 0 && ` (${(c.weekdays ?? []).map((d) => DAYS[d]).join(", ")} only)`}</li>
              <li>✅ ${c.max_price_per_ticket} or less per ticket, including fees</li>
              <li>✅ {c.quantity} seat{(c.quantity ?? 1) > 1 ? "s" : ""}</li>
              {(c.exclude_sections ?? []).map((s) => <li key={s}>✅ Not {s}</li>)}
              {(c.preferences ?? []).map((p) => <li key={p} className="text-slate-500">☆ Nice to have: {p}</li>)}
            </ul>
            <button onClick={() => setEditing(true)} className="mt-3 text-sm underline">Edit</button>
          </Card>
        ) : (
          <Card>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm">Team / artist / show
                <input className={inputClass} value={draft.performer}
                  onChange={(e) => setDraft({ ...draft, performer: e.target.value })} /></label>
              <label className="text-sm">Max price per ticket ($, incl. fees)
                <input type="number" className={inputClass} value={draft.max_price_per_ticket}
                  onChange={(e) => setDraft({ ...draft, max_price_per_ticket: Number(e.target.value) })} /></label>
              <label className="text-sm">From
                <input type="date" className={inputClass} value={draft.date_from}
                  onChange={(e) => setDraft({ ...draft, date_from: e.target.value })} /></label>
              <label className="text-sm">To
                <input type="date" className={inputClass} value={draft.date_to}
                  onChange={(e) => setDraft({ ...draft, date_to: e.target.value })} /></label>
              <label className="text-sm">Seats
                <input type="number" min={1} className={inputClass} value={draft.quantity ?? 1}
                  onChange={(e) => setDraft({ ...draft, quantity: Number(e.target.value) })} /></label>
            </div>
            <div className="mt-3 flex gap-2">
              <Button disabled={busy} onClick={saveEdits}>Save</Button>
              <Button variant="ghost" onClick={() => { setDraft(watch.checklist); setEditing(false); }}>Cancel</Button>
            </div>
          </Card>
        )}
        {(watch.questions ?? []).length > 0 && (
          <div className="rounded-lg bg-amber-50 p-3 text-sm">
            {(watch.questions ?? []).map((q) => <p key={q}>❓ {q} <span className="text-slate-500">(edit above if needed)</span></p>)}
          </div>
        )}
        <p className="text-sm text-slate-600">
          Watching {(watch.events ?? []).length} matching events. If no match appears before they happen, you're refunded automatically.
        </p>
        <ErrorText error={error} />
        <Button disabled={busy || editing} onClick={confirm}>Correct, start watching for ${watch.price_usd}</Button>
      </section>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-4 py-8">
      <h1 className="text-2xl font-bold">Start a watch</h1>
      <label className="block">
        <span className="font-semibold">What tickets are you looking for?</span>
        <textarea required rows={3} value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="Knicks under $80, any Friday in November, 2 seats, not the upper level"
          className={`${inputClass} mt-1`} />
      </label>
      <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email for alerts"
        className={inputClass} />
      <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone for texts, e.g. +12125551234 (optional)"
        className={inputClass} />
      {phone && (
        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          Text me ticket alerts for this watch. Msg & data rates may apply. Reply STOP anytime.
        </label>
      )}
      <ErrorText error={error} />
      <Button type="submit" disabled={busy}>{busy ? "Building your checklist…" : "Next"}</Button>
    </form>
  );
}
