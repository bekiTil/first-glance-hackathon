// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function FreeEvents() {
  return (
    <TodoPage
      title="Free in NYC tonight"
      spec={[
        "api.freeEvents(\"tonight\") → list of title/when/where/url",
        "Call to action: start a watch for paid tickets",
      ]}
    />
  );
}
