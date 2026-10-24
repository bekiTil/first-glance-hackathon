// Routes. Owner: Yared. The URLs are a contract: the backend links to /watch/:id, /thanks, /me?token=.
import { Link, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import NewWatch from "./pages/NewWatch";
import WatchStatus from "./pages/WatchStatus";
import MyWatches from "./pages/MyWatches";
import FreeEvents from "./pages/FreeEvents";
import CompanyLog from "./pages/CompanyLog";
import Thanks from "./pages/Thanks";

export default function App() {
  return (
    <div className="min-h-screen bg-white text-slate-900">
      <header className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
        <Link to="/" className="text-lg font-bold">
          🎟 Ticket Watch
        </Link>
        <nav className="flex gap-4 text-sm text-slate-600">
          <Link to="/events">Free tonight</Link>
          <Link to="/company">Company log</Link>
          <Link to="/me">My watches</Link>
        </nav>
      </header>
      <main className="mx-auto max-w-4xl px-4 pb-16">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/watch/new" element={<NewWatch />} />
          <Route path="/watch/:id" element={<WatchStatus />} />
          <Route path="/me" element={<MyWatches />} />
          <Route path="/events" element={<FreeEvents />} />
          <Route path="/company" element={<CompanyLog />} />
          <Route path="/thanks" element={<Thanks />} />
        </Routes>
      </main>
    </div>
  );
}
