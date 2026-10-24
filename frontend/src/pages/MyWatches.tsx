// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function MyWatches() {
  return (
    <TodoPage
      title="My watches"
      spec={[
        "No token: email form → api.login (magic link)",
        "With ?token=: api.myWatches(token) → list linking to /watch/:id",
      ]}
    />
  );
}
