// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function NewWatch() {
  return (
    <TodoPage
      title="Start a watch"
      spec={[
        "Form: query text, email, phone (optional), SMS consent checkbox → api.createWatch",
        "Show the returned checklist (✅ items) + questions; allow edits → api.updateChecklist",
        "Button \"Correct, start watching for $X\" → api.confirmWatch → redirect to checkout_url",
      ]}
    />
  );
}
