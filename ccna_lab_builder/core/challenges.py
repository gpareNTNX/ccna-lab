"""Separate catalogs for converted and advanced Cisco challenge material."""

from __future__ import annotations

from ccna_lab_builder.data.advanced_cisco_labs import advanced_cisco_labs
from ccna_lab_builder.data.challenge_labs import challenge_labs


class ChallengeCatalog:
    """Keep non-numeric challenge IDs isolated from CCNA labs 01-37."""

    def __init__(self):
        self._challenges = challenge_labs() + advanced_cisco_labs()
        ids = [item["id"] for item in self._challenges]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate challenge lab id detected.")
        if any(item_id.isdigit() for item_id in ids):
            raise ValueError("Challenge IDs must not overlap the numeric CCNA lab catalog.")
        if any(not item.get("buildable") for item in self._challenges):
            raise ValueError("Challenge catalog may contain only buildable labs.")

    def all(self):
        return list(self._challenges)

    def archive(self):
        """Compatibility shim: unconverted Packet Tracer labs are no longer exposed."""
        return []

    def get(self, challenge_id):
        wanted = str(challenge_id)
        for challenge in self._challenges:
            if challenge["id"] == wanted:
                return challenge
        raise KeyError(challenge_id)
