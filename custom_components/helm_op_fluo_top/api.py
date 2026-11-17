"""Minimal client for the Helm Op Fluo Top GraphQL API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import aiohttp

from .const import API_URL

# Only ask for what the integration needs. Badge participants are limited to
# id + count so classmates' names never reach Home Assistant.
FIND_PUPIL_QUERY = """
query find_pupil($guard: String, $token: String) {
  find_pupil(guard: $guard, token: $token) {
    id
    firstname
    edition { id name }
    points { total }
    vouchers { type code }
    school_class {
      name
      individual
      school { name }
      badges_grouped {
        id
        title
        pupils_merged { id count }
      }
    }
  }
}
"""

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=20)


class HoftError(Exception):
    """Base error."""


class HoftConnectionError(HoftError):
    """The API could not be reached or returned something unexpected."""


class HoftAuthError(HoftError):
    """The code is not (or no longer) valid."""


@dataclass(slots=True)
class Badge:
    """A badge the pupil earned."""

    id: int
    title: str
    count: int


@dataclass(slots=True)
class PupilData:
    """Normalised data for one pupil in their most recent edition."""

    pupil_id: int
    firstname: str
    edition_id: int
    edition_name: str
    points: int
    school: str | None
    class_name: str | None
    vouchers: list[dict[str, Any]] = field(default_factory=list)
    badges: list[Badge] = field(default_factory=list)

    @property
    def badge_count(self) -> int:
        """Total number of badges earned (a badge can be earned more than once)."""
        return sum(badge.count for badge in self.badges)


class HoftClient:
    """Talks to the GraphQL endpoint used by helmopfluotop.vsv.be."""

    def __init__(self, session: aiohttp.ClientSession, code: str) -> None:
        self._session = session
        self._code = code.strip()

    async def async_get_pupil(self) -> PupilData:
        """Fetch the pupil linked to the code, for the newest edition."""
        payload = {
            "query": FIND_PUPIL_QUERY,
            "variables": {"guard": "token", "token": self._code},
        }
        try:
            async with self._session.post(
                API_URL, json=payload, timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status >= 500:
                    raise HoftConnectionError(f"Server error {resp.status}")
                body = await resp.json(content_type=None)
        except (TimeoutError, aiohttp.ClientError, ValueError) as err:
            raise HoftConnectionError(str(err)) from err

        if not isinstance(body, dict):
            raise HoftConnectionError("Unexpected response")

        errors = body.get("errors") or []
        pupils = (body.get("data") or {}).get("find_pupil")

        if errors and not pupils:
            messages = " ".join(str(e.get("message", "")) for e in errors)
            if "token" in messages.lower() or "not found" in messages.lower():
                raise HoftAuthError(messages)
            raise HoftConnectionError(messages or "GraphQL error")

        if not pupils:
            raise HoftAuthError("No pupil found for this code")

        return _parse_latest(pupils)


def _parse_latest(pupils: list[dict[str, Any]]) -> PupilData:
    """Pick the newest edition and flatten it."""
    pupil = max(pupils, key=lambda p: int((p.get("edition") or {}).get("id") or 0))
    pupil_id = int(pupil["id"])
    edition = pupil.get("edition") or {}
    school_class = pupil.get("school_class") or {}

    badges: list[Badge] = []
    for badge in school_class.get("badges_grouped") or []:
        for entry in badge.get("pupils_merged") or []:
            if int(entry.get("id", -1)) == pupil_id:
                badges.append(
                    Badge(
                        id=int(badge["id"]),
                        title=str(badge.get("title") or ""),
                        count=int(entry.get("count") or 1),
                    )
                )

    return PupilData(
        pupil_id=pupil_id,
        firstname=str(pupil.get("firstname") or ""),
        edition_id=int(edition.get("id") or 0),
        edition_name=str(edition.get("name") or ""),
        points=int((pupil.get("points") or {}).get("total") or 0),
        school=(school_class.get("school") or {}).get("name"),
        class_name=school_class.get("name"),
        vouchers=list(pupil.get("vouchers") or []),
        badges=badges,
    )
