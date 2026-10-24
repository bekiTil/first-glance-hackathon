// Email magic link -> list of watches. Owner: Yared.
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type WatchOut } from "../api/client";
import { Button, Card, ErrorText, inputClass } from "../ui";

export default function MyWatches() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [watches, setWatches] = useState<WatchOut[] | null>(null);

  useEffect(() => {
    if (token) api.myWatches(token).then(setWatches).catch((e) => setError(String(e.message ?? e)));
  }, [token]);

  if (watches) {
    return (
      <section className="space-y-3 py-8">
        <h1 className="text-2xl font-bold">My watches</h1>
        {watches.length === 0 && <p className="text-slate-500">No watches yet. <Link to="/watch/new" className="underline">Start one</Link>.</p>}
        {watches.map((w) => (
          <Link key={w.id} to={`/watch/${w.id}`} className="block">
            <Card>
              <p>{w.checklist.query}</p>
              <p className="mt-1 text-sm text-slate-500">{w.status.replaceAll("_", " ")}</p>
            </Card>
          </Link>
        ))}
      </section>
    );
  }
  return (
    <form className="space-y-3 py-8" onSubmit={(e) => {
      e.preventDefault();
      setError("");
      api.login(email).then((r) => setMessage(r.message ?? "")).catch((err) => setError(String(err.message ?? err)));
    }}>
      <h1 className="text-2xl font-bold">My watches</h1>
      <p className="text-slate-600">No password: we'll email you a one-time login link.</p>
      <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className={inputClass} />
      <Button type="submit">Email me a login link</Button>
      {message && <p className="text-sm text-slate-600">{message}</p>}
      <ErrorText error={error} />
    </form>
  );
}
