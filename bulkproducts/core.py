"""BulkProducts plugin for InvenTree.

Initial scaffold:
- SettingsMixin: configurable defaults (for later import / stock-in workflow)
- ActionMixin: a 'dry-run' bulk import endpoint we can evolve into real creation + stock-in
"""

from __future__ import annotations

from typing import Any

from plugin import InvenTreePlugin
from plugin.mixins import ActionMixin, SettingsMixin

from .version import __version__


class BulkProductsPlugin(ActionMixin, SettingsMixin, InvenTreePlugin):
    """Create multiple parts (and later: stock them in) in one step."""

    NAME = "BulkProductsPlugin"
    SLUG = "bulkproducts"
    TITLE = "Bulk Products"
    DESCRIPTION = "Bulk-create parts and (optionally) stock them in"

    AUTHOR = "Grischa Media"
    LICENSE = "MIT"
    WEBSITE = "https://github.com/grischamedia/ch.grischamedia.inventree.bulkproducts"

    VERSION = __version__
    MIN_VERSION = "1.1.7"

    # Call via POST /api/action/  {"action":"bulkproducts.dry_run","data":{...}}
    ACTION_NAME = "bulkproducts.dry_run"

    SETTINGS = {
        "ALLOW_CREATE": {
            "name": "Allow create",
            "description": "If enabled, the plugin is allowed to create records (when we add non-dry-run actions)",
            "validator": bool,
            "default": False,
        },
        "DEFAULT_STOCK_LOCATION_ID": {
            "name": "Default stock location ID",
            "description": "Optional default location (database ID) for stock-in operations",
            "validator": int,
            "default": 0,
        },
    }

    def _validate_payload(self, data: Any) -> tuple[list[dict[str, Any]], list[str]]:
        """Validate incoming payload.

        Expected structure:
        {
          "parts": [
            {"name": "...", "ipn": "...", "description": "...", "quantity": 5},
            ...
          ]
        }
        """
        errors: list[str] = []

        if not isinstance(data, dict):
            return [], ["data must be an object"]

        parts = data.get("parts", [])

        if not isinstance(parts, list) or len(parts) == 0:
            return [], ["data.parts must be a non-empty list"]

        normalized: list[dict[str, Any]] = []

        for idx, item in enumerate(parts):
            if not isinstance(item, dict):
                errors.append(f"parts[{idx}] must be an object")
                continue

            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"parts[{idx}].name is required")

            ipn = item.get("ipn", None)
            if ipn is not None and (not isinstance(ipn, str) or not ipn.strip()):
                errors.append(f"parts[{idx}].ipn must be a non-empty string if provided")

            qty = item.get("quantity", 0)
            if qty is None:
                qty = 0
            if not isinstance(qty, int) or qty < 0:
                errors.append(f"parts[{idx}].quantity must be an integer >= 0")

            normalized.append(
                {
                    "name": (name or "").strip() if isinstance(name, str) else "",
                    "ipn": ipn.strip() if isinstance(ipn, str) else None,
                    "description": item.get("description", "") if isinstance(item.get("description", ""), str) else "",
                    "quantity": qty,
                }
            )

        return normalized, errors

    def perform_action(self, user=None, data=None):
        """Dry-run only (no side effects)."""
        return None

    def get_result(self, user=None, data=None):
        parts, errors = self._validate_payload(data)
        return len(errors) == 0 and len(parts) > 0

    def get_info(self, user=None, data=None):
        parts, errors = self._validate_payload(data)

        # What we *would* do (first iteration)
        plan = []
        for p in parts:
            plan.append(
                {
                    "create_part": {"name": p["name"], "ipn": p["ipn"]},
                    "stock_in": {"quantity": p["quantity"]} if p["quantity"] else None,
                }
            )

        return {
            "mode": "dry-run",
            "errors": errors,
            "count": len(parts),
            "plan": plan,
            "settings": self.get_settings_dict(),
            "user": getattr(user, "username", None),
        }

