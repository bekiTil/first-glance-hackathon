// Owner: Yared. Replace the placeholder with the real page.
import TodoPage from "./_TodoPage";

export default function TestTaker() {
  return (
    <TodoPage
      title="Look at this for 5 seconds"
      spec={[
        "Route /t/:id?teracSubmissionId=... (Terac participants land here) → api.getTestPage(id, participant)",
        "Intro: \"You will see a website for 5 seconds. Then 2 quick questions.\" + Start button",
        "Show hero (headline, subhead, cta) full screen for page.seconds, then hide it",
        "Ask \"What does this company do?\" (text) + \"How likely are you to sign up? 1-5\" → api.submitAnswer with page.arm",
        "Done screen: \"Go back to Terac and mark the task complete\"",
      ]}
    />
  );
}
