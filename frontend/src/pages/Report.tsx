// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function Report() {
  return (
    <TodoPage
      title="Your FirstGlance report"
      spec={[
        "Route /report/:id (Whop returns here with ?paid=1; report email links here) → api.getTest, poll every 5 s",
        "Status line: paid → testing (\"7 of 10 people answered\") → delivered / refunded",
        "Delivered: winner, understood rate per version (e.g. 3/5 vs 5/5), avg sign-up score, sample answers, the rewrite to copy",
        "Contact form → api.contact",
      ]}
    />
  );
}
