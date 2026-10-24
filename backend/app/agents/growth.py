"""Growth agent. Owner: Yared.

Every 30 min: take the CEO's top priority, research it with Exa, write ONE honest post, pass it through
guardrails, then publish to Bluesky (if configured) and always to the "Agent picks" section of our own
landing page (it reads published_post entries from the Company Log).
"""

from app.agents.base import Agent, AgentContext
from app.config import settings
from app.enums import AgentName, OutboundKind, StateKey
from app.integrations import bluesky, exa, llm
from app.models import Job

DEFAULT_PRIORITY = "Get the first customers: founders who just launched a landing page"

SYSTEM = (
    "You are the Growth agent of FirstGlance, a company run entirely by AI agents: for $15, ~10 real people "
    "see your landing page for 5 seconds and say what they think you do; an AI rewrite is tested against "
    "yours and you get proof of which works, refunded if ours doesn't win. Write ONE short, honest post for "
    "founders about the priority, using a concrete fact from the research if there is one. "
    "No hype, no invented numbers, no hashtag spam. The post must contain the literal text {LINK} once."
)
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["post", "headline", "reason"],
    "properties": {
        "post": {"type": "string", "description": "Under 250 characters, contains {LINK} once"},
        "headline": {"type": "string", "description": "Short title for our site's Agent picks section"},
        "reason": {"type": "string", "description": "Why this post serves the priority"},
    },
}


class GrowthAgent(Agent):
    name = AgentName.growth
    every_minutes = 30

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        priorities = ctx.get_state(StateKey.priorities) or [DEFAULT_PRIORITY]
        priority = priorities[0]
        research = exa.search(f"{priority} landing page first impression clarity", n=3)
        draft = llm.ask_json(
            SYSTEM,
            f"Priority: {priority}\nResearch:\n"
            + "\n".join(f"- {r['title']}: {r['text'][:300]} ({r['url']})" for r in research),
            SCHEMA,
            mock={
                "post": "Visitors decide in seconds whether they get your startup. We show your page to real "
                "people for 5 seconds, rewrite what confused them, and prove which version wins. $15: {LINK}",
                "headline": "Do strangers get your startup in 5 seconds?",
                "reason": "Founders polishing a launch page are the fastest first customers.",
            },
        )
        link = f"{settings.public_web_url.rstrip('/')}/test/new"
        text = (
            draft["post"].replace("{LINK}", link) if "{LINK}" in draft["post"] else f"{draft['post']} {link}"
        )
        channel = "bluesky" if bluesky.enabled() else "site"
        if not ctx.check(OutboundKind.post, text, channel=channel):
            return
        url = None
        if channel == "bluesky":
            try:
                url = bluesky.post(text, link)
            except Exception as e:
                channel = "site"
                ctx.log("post_failed", f"Bluesky rejected the post ({e}); published on our site only.")
        ctx.log(
            "published_post",
            draft["reason"],
            channel=channel,
            post=text,
            url=url,
            headline=draft["headline"],
            priority=priority,
            sources=[r["url"] for r in research],
        )
