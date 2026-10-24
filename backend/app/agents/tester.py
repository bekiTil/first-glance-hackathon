"""Tester agent (the product). Owner: Bereket.

TODO(Bereket): implement run(). Spec:
- Runs every 2 min AND on run_test jobs (payload {"test_id": public_id}). Handles kind=customer
  and kind=self tests the same way.
- status=paid (or a new self test): launch ONE Terac study for the test:
    terac.create_study(title, description, task_url=f"{PUBLIC_WEB_URL}/t/{public_id}",
                       participants=settings.test_participants, minutes=2)
  then terac.launch(id). Save terac_id, terac_quote, launched_at, status=testing.
  If PUBLIC_WEB_URL isn't https, don't launch; log "waiting_for_public_url" once.
  If the quote says affordable=False, log it and leave status=paid (Finance refunds after a while).
- status=testing: when both arms have >= settings.min_answers_per_arm TestAnswers, or
  settings.test_timeout_minutes passed since launched_at with >= 1 answer per arm:
    grade every answer: llm.ask_json "does this answer match what_you_do?" -> TestAnswer.understood
    build schemas.TestResults (per arm: responses, understood, understood_rate, avg_signup,
    up to 5 sample answers); winner = rewrite if its understood_rate is higher (tie -> compare
    avg_signup; still tied -> tie). summary like "3/5 understood yours, 5/5 understood ours".
    Save results, delivered_at, status=delivered.
- For kind=customer: email the report (notify.send_email, after ctx.check(OutboundKind.email, ...))
  with the winner, the rewrite copy and the link {PUBLIC_WEB_URL}/report/{public_id}.
- ctx.log every step ("launched_test", "graded_test", "delivered_report") with numbers, no emails.
Refunds are NOT done here: Finance refunds delivered tests where winner != rewrite.
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName, JobType
from app.models import Job


class TesterAgent(Agent):
    name = AgentName.tester
    every_minutes = 2
    handles = (JobType.run_test,)

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Bereket): tester")
