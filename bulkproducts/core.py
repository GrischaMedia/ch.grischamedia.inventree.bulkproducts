"""BulkProducts plugin for InvenTree.

Provides a custom plugin page under:

- /plugin/bulk-products/

This page can bulk-create parts (and optionally stock them in).
"""

from __future__ import annotations

from typing import Any

import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.urls import path

from plugin import InvenTreePlugin
from plugin.mixins import ActionMixin, NavigationMixin, SettingsMixin, UrlsMixin

from .version import __version__


class BulkProductsPlugin(
    ActionMixin, SettingsMixin, UrlsMixin, NavigationMixin, InvenTreePlugin
):
    """Create multiple parts (and later: stock them in) in one step."""

    NAME = "BulkProductsPlugin"
    TITLE = "Bulk Products"
    SLUG = "bulk-products"
    DESCRIPTION = "Erstellt mehrere neue Teile in InvenTree und kann diese optional direkt einbuchen."

    AUTHOR = "GrischaMedia.ch"
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

    NAVIGATION_TAB_ICON = "fas fa-boxes"
    NAVIGATION = [{"name": "Bulk Products", "link": "plugin:bulk-products:index"}]

    def setup_urls(self):
        """URLs exposed by this plugin."""

        return [
            path("", login_required(self.view_bulk_products), name="index"),
            path(
                "api/bulk-create/",
                login_required(self.api_bulk_create),
                name="api-bulk-create",
            ),
        ]

    @permission_required("part.view_partcategory", raise_exception=True)
    def view_bulk_products(self, request: HttpRequest):
        """Render the bulk-products page."""

        from part.models import PartCategory
        from stock.models import StockLocation

        categories = (
            PartCategory.objects.all()
            .select_related("parent")
            .order_by("tree_id", "lft")
        )

        locations = (
            StockLocation.objects.all()
            .select_related("parent")
            .order_by("tree_id", "lft")
        )

        context = {
            "plugin_title": self.TITLE,
            "categories": categories,
            "locations": locations,
            "default_location_id": int(
                self.get_setting("DEFAULT_STOCK_LOCATION_ID", backup_value=0) or 0
            ),
        }

        return render(request, "bulkproducts/bulk_products.html", context)

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

    @permission_required("part.add_part", raise_exception=True)
    def api_bulk_create(self, request: HttpRequest):
        """Create parts and optionally stock them in.

        POST JSON:
        {
          "items": [
            {
              "category_id": 1,
              "name": "Widget A",
              "description": "...",
              "ipn": "W-A",
              "quantity": 10,
              "location_id": 5
            }
          ]
        }
        """

        if request.method != "POST":
            return JsonResponse({"error": "method_not_allowed"}, status=405)

        if not bool(self.get_setting("ALLOW_CREATE", backup_value=False)):
            return JsonResponse(
                {
                    "error": "creation_disabled",
                    "detail": "Plugin setting ALLOW_CREATE is disabled",
                },
                status=400,
            )

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return JsonResponse({"error": "invalid_json"}, status=400)

        items = payload.get("items", [])
        if not isinstance(items, list) or len(items) == 0:
            return JsonResponse({"error": "items_required"}, status=400)

        from django.db.utils import IntegrityError
        from part.models import Part, PartCategory
        from stock.models import StockItem, StockLocation

        results: list[dict[str, Any]] = []

        default_location_id = int(
            self.get_setting("DEFAULT_STOCK_LOCATION_ID", backup_value=0) or 0
        )

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                results.append(
                    {"index": idx, "success": False, "error": "item_must_be_object"}
                )
                continue

            category_id = item.get("category_id")
            name = (item.get("name") or "").strip()
            description = (item.get("description") or "").strip()
            ipn = (item.get("ipn") or "").strip()
            quantity = item.get("quantity", 0)
            location_id = item.get("location_id", None)

            if not category_id or not name:
                results.append(
                    {
                        "index": idx,
                        "success": False,
                        "error": "missing_required_fields",
                        "fields": {"category_id": bool(category_id), "name": bool(name)},
                    }
                )
                continue

            try:
                qty = int(quantity or 0)
            except Exception:
                results.append(
                    {"index": idx, "success": False, "error": "invalid_quantity"}
                )
                continue

            if qty < 0:
                results.append(
                    {"index": idx, "success": False, "error": "invalid_quantity"}
                )
                continue

            if (location_id is None or location_id == "") and default_location_id > 0:
                location_id = default_location_id

            if qty > 0 and not location_id:
                results.append(
                    {
                        "index": idx,
                        "success": False,
                        "error": "location_required_for_stock_in",
                    }
                )
                continue

            try:
                category = PartCategory.objects.get(pk=int(category_id))
            except Exception:
                results.append(
                    {"index": idx, "success": False, "error": "invalid_category"}
                )
                continue

            location = None
            if qty > 0:
                try:
                    location = StockLocation.objects.get(pk=int(location_id))
                except Exception:
                    results.append(
                        {"index": idx, "success": False, "error": "invalid_location"}
                    )
                    continue

            try:
                with transaction.atomic():
                    part = Part.objects.create(
                        name=name,
                        description=description,
                        category=category,
                        IPN=ipn,
                    )

                    stock_item = None
                    if qty > 0 and location is not None:
                        stock_item = StockItem.objects.create(
                            part=part,
                            location=location,
                            quantity=Decimal(qty),
                        )

            except IntegrityError as e:
                results.append(
                    {
                        "index": idx,
                        "success": False,
                        "error": "integrity_error",
                        "detail": str(e),
                    }
                )
                continue
            except Exception as e:
                results.append(
                    {"index": idx, "success": False, "error": "exception", "detail": str(e)}
                )
                continue

            results.append(
                {
                    "index": idx,
                    "success": True,
                    "part": {
                        "id": part.pk,
                        "name": part.name,
                        "ipn": getattr(part, "IPN", ""),
                        "url": part.get_absolute_url() if hasattr(part, "get_absolute_url") else None,
                    },
                    "stock_item": {
                        "id": stock_item.pk if stock_item is not None else None,
                        "quantity": qty,
                        "location_id": int(location_id) if location_id else None,
                    },
                }
            )

        return JsonResponse({"results": results})

