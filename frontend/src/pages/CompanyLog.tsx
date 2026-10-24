// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function CompanyLog() {
  return (
    <TodoPage
      title="Company log"
      spec={[
        "Judges page: api.stats() tiles (revenue, active watches, alerts, purchases)",
        "api.companyLog() feed: agent badge, action, reason, time; refresh every ~10s",
        "Show Terac before/after when Study 2 is done",
      ]}
    />
  );
}
