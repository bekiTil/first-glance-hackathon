// Free NYC events found by our agent with Exa. Brings visitors in. Owner: Yared.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type FreeEvent } from "../api/client";
import { Card, ErrorText } from "../ui";

export default function FreeEvents() {
  const [when, setWhen] = useState("tonight");
  const [events, setEvents] = useState<FreeEvent[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setEvents(null);
    setError("");
    api.freeEvents(when).then(setEvents).catch((e) => setError(String(e.message ?? e)));
  }, [when]);

  return (
    <section className="py-8">
      <h1 className="text-2xl font-bold">Free in NYC</h1>
      <p className="text-sm text-slate-500">Found by our AI agent on Luma and Eventbrite.</p>
      <div className="mt-4 flex gap-2">
        {["tonight", "this weekend"].map((w) => (
          <button key={w} onClick={() => setWhen(w)}
            className={`rounded-full px-3 py-1 text-sm ${when === w ? "bg-slate-900 text-white" : "bg-slate-100"}`}>
            {w}
          </button>
        ))}
      </div>
      <ErrorText error={error} />
      {!events && !error && <p className="mt-4 text-slate-500">Searching…</p>}
      <div className="mt-4 space-y-3">
        {(events ?? []).map((e) => (
          <a key={e.url} href={e.url} target="_blank" rel="noreferrer" className="block">
            <Card>
              <p className="font-semibold">{e.title}</p>
              {e.summary && <p className="mt-1 line-clamp-2 text-sm text-slate-600">{e.summary}</p>}
              <p className="mt-1 text-xs text-slate-400">{[e.when, e.where].filter(Boolean).join(" · ")}</p>
            </Card>
          </a>
        ))}
      </div>
      <p className="mt-8">Want paid tickets for less? <Link to="/watch/new" className="underline">Start a $3 watch</Link>.</p>
    </section>
  );
}
