// Routes. Owner: Yared. The URLs are a contract: Terac sends people to /t/:id, Whop returns buyers to
// /report/:id?paid=1, and report emails link to /report/:id.
import { Link, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import NewTest from "./pages/NewTest";
import Report from "./pages/Report";
import TestTaker from "./pages/TestTaker";
import CompanyLog from "./pages/CompanyLog";

export default function App() {
  return (
    <div className="min-h-screen bg-white text-slate-900">
      <header className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
        <Link to="/" className="text-lg font-bold">
          👀 FirstGlance
        </Link>
        <nav className="flex gap-4 text-sm text-slate-600">
          <Link to="/test/new">Test my page</Link>
          <Link to="/company">Company log</Link>
        </nav>
      </header>
      <main className="mx-auto max-w-4xl px-4 pb-16">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/test/new" element={<NewTest />} />
          <Route path="/report/:id" element={<Report />} />
          <Route path="/t/:id" element={<TestTaker />} />
          <Route path="/company" element={<CompanyLog />} />
        </Routes>
      </main>
    </div>
  );
}
