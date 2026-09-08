"""Catalog for isolated Nutanix bonus labs."""

from __future__ import annotations

from ccna_lab_builder.data.nutanix_bonus_expansion import nutanix_bonus_expansion_labs
from ccna_lab_builder.data.nutanix_bonus_labs import nutanix_bonus_labs


class NutanixBonusCatalog:
    """Keep Nutanix bonus IDs separate from CCNA and Cisco Challenge catalogs."""

    def __init__(self):
        self._labs = nutanix_bonus_labs() + nutanix_bonus_expansion_labs()
        ids = [item["id"] for item in self._labs]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate Nutanix bonus lab id detected.")
        if any(not item_id.startswith("NTNX-B") for item_id in ids):
            raise ValueError("Nutanix bonus IDs must start with NTNX-B.")
        if any(not item.get("buildable") for item in self._labs):
            raise ValueError("Nutanix bonus catalog may contain only buildable labs.")

    def all(self):
        return list(self._labs)

    def get(self, lab_id):
        wanted = str(lab_id)
        for lab in self._labs:
            if lab["id"] == wanted:
                return lab
        raise KeyError(lab_id)
