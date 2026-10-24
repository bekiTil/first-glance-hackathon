// After payment (Whop redirects to /watch/:id?paid=1): status + phone verification. Owner: Yared.
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { api, type WatchOut } from "../api/client";
import { Button, Card, ErrorText, inputClass } from "../ui";

const STATUS_TEXT: Record<string, string> = {
  draft: "not started yet", awaiting_payment: "waiting for payment", active: "active: we're watching",
  purchased: "done: you bought tickets 🎉", expired: "finished", refunded: "refunded (no match found)",
  cancelled: "cancelled",
};

export default function WatchStatus() {
  const { id = "" } = useParams();
  const [params] = useSearchParams();
  const [watch, setWatch] = useState<WatchOut | null>(null);
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const load = () => api.getWatch(id).then(setWatch).catch((e) => setError(String(e.message ?? e)));
  useEffect(() => {
    load();
    // payment is processed by the Finance agent a few seconds after checkout
    const timer = setInterval(load, 5_000);
    return () => clearInterval(timer);
  }, [id]);

  const act = (fn: () => Promise<unknown>) => () => {
    setError("");
    fn().catch((e) => setError(String(e.message ?? e)));
  };

  if (!watch) return <section className="py-8"><ErrorText error={error} />{!error && "Loading…"}</section>;
  return (
    <section className="space-y-4 py-8">
      {params.get("paid") && watch.status !== "active" && watch.status === "awaiting_payment" && (
        <p className="rounded-lg bg-green-50 p-3 text-sm">Payment received. Activating your watch…</p>
      )}
      <h1 className="text-2xl font-bold">Your watch is {STATUS_TEXT[watch.status] ?? watch.status}</h1>
      <Card>
        <p className="text-slate-700">“{watch.checklist.query}”</p>
        <p className="mt-2 text-sm text-slate-500">
          Up to ${watch.checklist.max_price_per_ticket}/ticket · {watch.checklist.quantity} seat(s) ·
          {" "}{(watch.events ?? []).length} events being checked every 15 minutes
        </p>
      </Card>
      {!watch.phone_verified && (
        <Card>
          <p className="font-semibold">Get alerts by text too</p>
          {!sent ? (
            <div className="mt-2 flex gap-2">
              <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+12125551234" className={inputClass} />
              <Button onClick={act(() => api.sendCode(id, phone).then(() => setSent(true)))}>Send code</Button>
            </div>
          ) : (
            <div className="mt-2 flex gap-2">
              <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="6-digit code" className={inputClass} />
              <Button onClick={act(() => api.verifyCode(phone, code).then((r) => {
                if (!r.verified) throw new Error("That code didn't match. Try again.");
                return load();
              }))}>Verify</Button>
            </div>
          )}
        </Card>
      )}
      <ErrorText error={error} />
    </section>
  );
}
