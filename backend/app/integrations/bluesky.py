"""Bluesky posting for the Growth agent (free public API, no extra package). Owner: Yared.

Set BLUESKY_HANDLE + BLUESKY_APP_PASSWORD (Bluesky -> Settings -> App passwords). Not set = disabled.
"""

import httpx

from app.config import settings
from app.db_time import utcnow

PDS = "https://bsky.social/xrpc"


def enabled() -> bool:
    return bool(settings.bluesky_handle and settings.bluesky_app_password)


def post(text: str, link: str | None = None) -> str:
    """Publish a post; returns its web URL. `link` (if inside text) becomes clickable."""
    text = text if len(text) <= 295 else text[:292] + "..."
    with httpx.Client(timeout=20) as client:
        session = client.post(
            f"{PDS}/com.atproto.server.createSession",
            json={"identifier": settings.bluesky_handle, "password": settings.bluesky_app_password},
        )
        session.raise_for_status()
        auth = session.json()
        record: dict = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": utcnow().isoformat(timespec="milliseconds") + "Z",
        }
        if link and link in text:
            start = len(text[: text.index(link)].encode())
            record["facets"] = [
                {
                    "index": {"byteStart": start, "byteEnd": start + len(link.encode())},
                    "features": [{"$type": "app.bsky.richtext.facet#link", "uri": link}],
                }
            ]
        created = client.post(
            f"{PDS}/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {auth['accessJwt']}"},
            json={"repo": auth["did"], "collection": "app.bsky.feed.post", "record": record},
        )
        created.raise_for_status()
    rkey = created.json()["uri"].rsplit("/", 1)[-1]
    return f"https://bsky.app/profile/{settings.bluesky_handle}/post/{rkey}"
