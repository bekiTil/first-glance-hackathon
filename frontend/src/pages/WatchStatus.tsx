// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function WatchStatus() {
  return (
    <TodoPage
      title="Watch status"
      spec={[
        "Route /watch/:id (Whop redirects here with ?paid=1) → api.getWatch(id)",
        "Show status + checklist + events being watched",
        "If phone not verified: api.sendCode → code input → api.verifyCode (mock code 123456)",
      ]}
    />
  );
}
