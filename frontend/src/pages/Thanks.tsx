// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function Thanks() {
  return (
    <TodoPage
      title="Thanks"
      spec={[
        "Route /thanks?action=bought|keep|reject (email buttons redirect here)",
        "Short message per action",
      ]}
    />
  );
}
