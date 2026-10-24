// Landing page. The hero copy comes from /api/landing-copy, so the Research agent's winning
// version (tested with real people) goes live by itself. Owner: Yared.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type DecisionOut, type HeroCopy } from "../api/client";
import { timeAgo } from "../ui";

const FALLBACK: HeroCopy = {
  headline: "Do people get your startup in 10 seconds?",
  subhead:
    "Real people see your landing page for 10 seconds. AI rewrites what confused them, and you get proof the new version works.",
  cta: "Test my page for $10",
};

const ICON = "h-5 w-5";
const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
const POWERED_BY = [
  { name: "Terac", role: "real people", icon: (
    <svg viewBox="0 0 24 24" className={ICON} {...stroke}><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" /><circle cx="17" cy="9" r="2.5" /><path d="M16 14.2A5 5 0 0 1 21.5 19" /></svg>
  ) },
  { name: "Whop", role: "payments", icon: (
    <svg viewBox="0 0 24 24" className={ICON} {...stroke}><rect x="2.5" y="5" width="19" height="14" rx="2.5" /><path d="M2.5 10h19M6.5 15h4" /></svg>
  ) },
  { name: "Exa", role: "web research", icon: (
    <svg viewBox="0 0 24 24" className={ICON} {...stroke}><circle cx="10.5" cy="10.5" r="6.5" /><path d="m20 20-4.8-4.8" /></svg>
  ) },
  { name: "Solari", role: "headless browsers", icon: (
    <svg viewBox="0 0 24 24" className={ICON} {...stroke}><rect x="2.5" y="4" width="19" height="16" rx="2.5" /><path d="M2.5 9h19M6 6.5h.01M9 6.5h.01" /></svg>
  ) },
  { name: "Claude", role: "AI agents", icon: (
    <svg viewBox="0 0 24 24" className={ICON} {...stroke}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8" /></svg>
  ) },
  { name: "Cloudflare", role: "hosting", icon: (
    <svg viewBox="0 0 24 24" className={ICON} {...stroke}><path d="M7 18h10.5a4 4 0 0 0 .5-7.97A6 6 0 0 0 6.3 9.2 4.5 4.5 0 0 0 7 18Z" /></svg>
  ) },
];

const STEPS = [
  ["Paste your URL", "Plus one sentence: what you do, and for whom. We read the top of your page and write a clearer version."],
  ["Real people look for 10 seconds", "Recruited through Terac. Half see your page, half see our rewrite, then tell us what they think you do."],
  ["Get proof, not opinions", "“2/5 understood yours, 4/5 understood ours.” Plus the exact copy to paste into your site."],
];

const FAQ = [
  ["Who are the testers?", "Real US adults recruited through Terac, a research marketplace. Not bots, not AI personas."],
  ["How long does it take?", "Usually about an hour, depending on how fast people pick up the task. Your report page updates live."],
  ["What if your rewrite doesn't win?", "Then you get your money back, automatically. Our agents check the results; nobody has to ask."],
  ["What exactly do people see?", "The top of your landing page (headline, subheading, main button) for 10 seconds, then two questions."],
  ["Is there really nobody running this?", "Really. Agents handle sales, testing, grading, payments and support. Every decision is public on the Company log."],
];

function HeroVisual() {
  return (
    <div className="relative">
      <div className="absolute -inset-3 -z-10 rounded-[2.25rem] bg-gradient-to-br from-brand-soft via-paper to-sun/40" />
      <div className="rounded-[1.75rem] border border-line bg-paper p-4 shadow-xl shadow-ink/5 sm:p-6">
        {/* fake browser window showing a page being tested */}
        <div className="overflow-hidden rounded-2xl border border-line bg-white">
          <div className="flex items-center gap-1.5 border-b border-line bg-cream px-3 py-2">
            <span className="h-2.5 w-2.5 rounded-full bg-[#f87171]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#fbbf24]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#34d399]" />
            <span className="ml-3 rounded-md bg-white px-2 py-0.5 text-[11px] text-muted">yourstartup.com</span>
          </div>
          <div className="space-y-3 px-6 py-10 text-center">
            <div className="mx-auto h-4 w-3/4 rounded-full bg-ink/80" />
            <div className="mx-auto h-4 w-1/2 rounded-full bg-ink/80" />
            <div className="mx-auto mt-4 h-2.5 w-2/3 rounded-full bg-ink/15" />
            <div className="mx-auto h-2.5 w-1/2 rounded-full bg-ink/15" />
            <div className="mx-auto mt-5 h-8 w-32 rounded-full bg-brand" />
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl border border-line bg-cream p-3">
            <p className="text-xs text-muted">Your version</p>
            <p className="font-display text-2xl font-semibold">2/5 <span className="text-sm font-normal text-muted">got it</span></p>
          </div>
          <div className="rounded-xl border-2 border-brand bg-brand-soft p-3">
            <p className="text-xs text-brand-dark">Our rewrite</p>
            <p className="font-display text-2xl font-semibold text-brand-dark">4/5 <span className="text-sm font-normal">got it</span></p>
          </div>
        </div>
      </div>
      {/* floating chips */}
      <div className="absolute -top-4 left-8 hidden items-center gap-2 rounded-full border border-line bg-white px-3 py-1.5 text-sm font-medium shadow-md sm:flex">
        <span className="h-2 w-2 animate-pulse rounded-full bg-[#ef4444]" /> 10 seconds, then hidden
      </div>
      <div className="absolute -right-5 top-28 hidden rounded-2xl border border-line bg-white px-3 py-2 text-sm shadow-md sm:block">
        <p className="text-xs text-muted">“What does this company do?”</p>
        <p className="font-medium">“Payroll for dentists?”</p>
      </div>
      <p className="mt-3 text-center text-xs text-muted">Illustration of a report</p>
    </div>
  );
}

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
      {/* hero */}
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-5 pb-16 pt-12 sm:pt-20 lg:grid-cols-[1.1fr_1fr]">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full bg-sun/70 px-3 py-1 text-sm font-medium text-ink">
            <span>👀 Real people, not AI personas<span className="hidden sm:inline"> · Run entirely by AI agents</span></span>
          </span>
          <h1 className="mt-6 font-display text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            {copy.headline}
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">{copy.subhead}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/test/new"
              className="rounded-full bg-ink px-6 py-3.5 font-semibold text-cream shadow-lg shadow-ink/10 transition hover:bg-brand-dark">
              {copy.cta || "Test my page"}
            </Link>
            <a href="#how" className="rounded-full border-2 border-ink px-6 py-3 font-semibold transition hover:bg-paper">
              See how it works
            </a>
          </div>
          <p className="mt-6 text-sm text-muted">
            <span className="font-semibold text-ink">Refund if our version doesn't win</span> · Results in about an hour · $10 per test
          </p>
        </div>
        <HeroVisual />
      </section>

      {/* powered by: slow, looping marquee (pauses on hover, still for reduced motion) */}
      <section className="border-y border-line bg-paper/60">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-5 py-6">
          <span className="shrink-0 text-xs font-medium uppercase tracking-[0.2em] text-muted">Powered by</span>
          <div className="relative overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)]">
            <div className="flex w-max animate-marquee gap-4 hover:[animation-play-state:paused]">
              {[...POWERED_BY, ...POWERED_BY].map((item, i) => (
                <div key={i} aria-hidden={i >= POWERED_BY.length}
                  className="flex shrink-0 items-center gap-3 rounded-full border border-line bg-paper py-2 pl-2 pr-5">
                  <span className="grid h-9 w-9 place-items-center rounded-full bg-brand-soft text-brand-dark">{item.icon}</span>
                  <span>
                    <span className="block font-display text-lg font-semibold leading-tight">{item.name}</span>
                    <span className="block text-xs text-muted">{item.role}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* how it works */}
      <section id="how" className="mx-auto max-w-6xl scroll-mt-20 px-5 py-20">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">How it works</p>
        <h2 className="mt-3 max-w-2xl font-display text-4xl font-semibold tracking-tight">
          Visitors decide in seconds. Find out what they decide.
        </h2>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {STEPS.map(([title, body], i) => (
            <div key={title} className="rounded-3xl border border-line bg-paper p-6">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-ink font-display text-lg text-cream">{i + 1}</span>
              <h3 className="mt-5 font-display text-2xl font-semibold">{title}</h3>
              <p className="mt-2 leading-relaxed text-muted">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* example */}
      <section className="mx-auto max-w-6xl px-5 pb-20">
        <div className="grid gap-6 rounded-[2rem] bg-ink p-8 text-cream sm:p-12 lg:grid-cols-2">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sun">Example</p>
            <h2 className="mt-3 font-display text-4xl font-semibold tracking-tight">Clever headlines lose. Clear ones win.</h2>
            <p className="mt-4 leading-relaxed text-cream/70">
              Most founders write for people who already get it. Strangers don't. We show you exactly what they think
              you do, in their own words.
            </p>
          </div>
          <div className="space-y-3">
            <div className="rounded-2xl bg-cream/10 p-5">
              <p className="text-xs uppercase tracking-wider text-cream/50">Before · 1 of 5 understood</p>
              <p className="mt-1 font-display text-2xl">“Synergy at the speed of your team.”</p>
              <p className="mt-2 text-sm italic text-cream/60">“A Slack competitor?” · “No idea, honestly.”</p>
            </div>
            <div className="rounded-2xl bg-cream p-5 text-ink">
              <p className="text-xs uppercase tracking-wider text-brand">After · 4 of 5 understood</p>
              <p className="mt-1 font-display text-2xl">“Payroll software for small dental clinics.”</p>
              <p className="mt-2 text-sm italic text-muted">“Payroll for dentists.” · “HR tool for dental offices.”</p>
            </div>
          </div>
        </div>
      </section>

      {/* pricing */}
      <section id="pricing" className="mx-auto max-w-6xl scroll-mt-20 px-5 pb-20">
        <div className="mx-auto max-w-xl rounded-[2rem] border border-line bg-paper p-8 text-center shadow-xl shadow-ink/5 sm:p-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand">Pricing</p>
          <p className="mt-4 font-display text-6xl font-semibold">$10</p>
          <p className="text-muted">per test · one page · no subscription</p>
          <ul className="mx-auto mt-6 max-w-sm space-y-2 text-left">
            {[
              "Real people see your page for 10 seconds",
              "A clearer rewrite, tested side by side",
              "Their answers, word for word",
              "Copy to paste into your site",
              "Automatic refund if ours doesn't win",
            ].map((item) => (
              <li key={item} className="flex gap-3"><span className="text-brand">✓</span>{item}</li>
            ))}
          </ul>
          <Link to="/test/new"
            className="mt-8 inline-block rounded-full bg-ink px-8 py-3.5 font-semibold text-cream transition hover:bg-brand-dark">
            Test my page
          </Link>
        </div>
      </section>

      {/* faq */}
      <section id="faq" className="mx-auto max-w-3xl scroll-mt-20 px-5 pb-20">
        <h2 className="text-center font-display text-4xl font-semibold tracking-tight">Questions</h2>
        <div className="mt-8 divide-y divide-line rounded-3xl border border-line bg-paper">
          {FAQ.map(([q, a]) => (
            <details key={q} className="group px-6 py-5">
              <summary className="flex cursor-pointer list-none items-center justify-between font-semibold">
                {q}
                <span className="text-xl text-muted transition group-open:rotate-45">+</span>
              </summary>
              <p className="mt-3 leading-relaxed text-muted">{a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* agent posts */}
      {picks.length > 0 && (
        <section className="mx-auto max-w-6xl px-5 pb-20">
          <h2 className="font-display text-3xl font-semibold">From our Growth agent</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {picks.map((p) => (
              <div key={p.id} className="rounded-3xl border border-line bg-paper p-5">
                <p className="font-semibold">{String(p.data.headline ?? "")}</p>
                <p className="mt-2 text-sm leading-relaxed text-muted">{String(p.data.post ?? "")}</p>
                <p className="mt-3 text-xs text-muted">{timeAgo(p.created_at)}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-8 text-sm text-muted">
          <span className="font-display text-lg font-semibold text-ink">FirstGlance</span>
          <span>
            Run entirely by AI agents. Every decision is public on the{" "}
            <Link to="/company" className="underline hover:text-ink">Company log</Link>.
          </span>
        </div>
      </footer>
    </>
  );
}
