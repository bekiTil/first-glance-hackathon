// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function NewTest() {
  return (
    <TodoPage
      title="Test my page"
      spec={[
        "Form: page URL, one sentence \"what do you do, for whom?\", email → api.createTest (takes ~10-20 s: show progress)",
        "Show original hero vs. our rewrite side by side + what happens next (10 real people, 5 seconds, ~1 hour)",
        "Button \"Test both for $X\" → api.confirmTest → redirect to checkout_url (Whop)",
        "Errors: 422 couldn't read that page → ask for a public URL",
      ]}
    />
  );
}
