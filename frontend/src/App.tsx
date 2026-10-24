// Routes + page shell. Owner: Yared. The URLs are a contract: Terac sends people to /t/:id, Whop returns buyers to
// /report/:id?paid=1, and report emails link to /report/:id.
import { Link, Route, Routes, useLocation } from "react-router-dom";
import Landing from "./pages/Landing";
import NewTest from "./pages/NewTest";
import Report from "./pages/Report";
import TestTaker from "./pages/TestTaker";
import CompanyLog from "./pages/CompanyLog";
import { ThemeToggle } from "./theme";

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2">
      <span className="grid h-8 w-8 place-items-center rounded-full bg-ink text-cream">
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.2">
          <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
          <circle cx="12" cy="12" r="3" fill="currentColor" />
        </svg>
      </span>
      <span className="font-display text-xl font-semibold tracking-tight">FirstGlance</span>
    </Link>
  );
}

export default function App() {
  const { pathname } = useLocation();
  const isLanding = pathname === "/";
  // Terac participants get a distraction-free page: no nav to wander off to.
  if (pathname.startsWith("/t/")) {
    return (
      <div className="min-h-screen">
        <Routes>
          <Route path="/t/:id" element={<TestTaker />} />
        </Routes>
      </div>
    );
  }
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-line bg-cream/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5">
          <Logo />
          <nav className="flex items-center gap-1 text-sm text-muted sm:gap-6">
            {isLanding && (
              <>
                <a href="#how" className="hidden hover:text-ink sm:block">How it works</a>
                <a href="#pricing" className="hidden hover:text-ink sm:block">Pricing</a>
                <a href="#faq" className="hidden hover:text-ink sm:block">FAQ</a>
              </>
            )}
            <Link to="/company" className="hidden hover:text-ink sm:block">Company log</Link>
            <ThemeToggle />
            <Link to="/test/new" className="ml-1 rounded-full bg-ink px-4 py-2 font-medium text-cream hover:bg-brand-dark">
              Test my page
            </Link>
          </nav>
        </div>
      </header>
      <main className={isLanding ? "" : "mx-auto max-w-3xl px-5 pb-20"}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/test/new" element={<NewTest />} />
          <Route path="/report/:id" element={<Report />} />
          <Route path="/company" element={<CompanyLog />} />
        </Routes>
      </main>
    </div>
  );
}
