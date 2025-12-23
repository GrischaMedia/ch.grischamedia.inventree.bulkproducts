import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from plugin.registry import registry


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required("part.view_partcategory", raise_exception=True), name='dispatch')
class BulkProductsView(TemplateView):
    template_name = "bulkproducts/bulk_products.html"

    def get_context_data(self, **kwargs):
        from part.models import PartCategory
        from stock.models import StockLocation

        ctx = super().get_context_data(**kwargs)

        default_location_id = 0
        plugin = registry.get_plugin("bulk-products")
        if plugin:
            try:
                default_location_id = int(
                    plugin.get_setting("DEFAULT_STOCK_LOCATION_ID", backup_value=0) or 0
                )
            except Exception:
                default_location_id = 0

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

        ctx["plugin_title"] = "Bulk Products"
        ctx["categories"] = categories
        ctx["locations"] = locations
        ctx["default_location_id"] = default_location_id
        ctx["csrf_token"] = get_token(self.request)
        return ctx


@login_required
@permission_required("part.add_part", raise_exception=True)
def bulk_create(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    plugin = registry.get_plugin("bulk-products")
    if not plugin:
        return JsonResponse({"error": "plugin_not_loaded"}, status=500)

    allow_create = bool(plugin.get_setting("ALLOW_CREATE", backup_value=False))
    if not allow_create:
        return JsonResponse(
            {"error": "creation_disabled", "detail": "Plugin setting ALLOW_CREATE is disabled"},
            status=400,
        )

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"error": "invalid_json"}, status=400)

    items = payload.get("items", [])
    if not isinstance(items, list) or len(items) == 0:
        return JsonResponse({"error": "items_required"}, status=400)

    from django.db import transaction
    from django.db.utils import IntegrityError
    from part.models import Part, PartCategory
    from stock.models import StockItem, StockLocation

    results = []

    try:
        default_location_id = int(plugin.get_setting("DEFAULT_STOCK_LOCATION_ID", backup_value=0) or 0)
    except Exception:
        default_location_id = 0

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            results.append({"index": idx, "success": False, "error": "item_must_be_object"})
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
            results.append({"index": idx, "success": False, "error": "invalid_quantity"})
            continue

        if qty < 0:
            results.append({"index": idx, "success": False, "error": "invalid_quantity"})
            continue

        if (location_id is None or location_id == "") and default_location_id > 0:
            location_id = default_location_id

        if qty > 0 and not location_id:
            results.append({"index": idx, "success": False, "error": "location_required_for_stock_in"})
            continue

        try:
            category = PartCategory.objects.get(pk=int(category_id))
        except Exception:
            results.append({"index": idx, "success": False, "error": "invalid_category"})
            continue

        location = None
        if qty > 0:
            try:
                location = StockLocation.objects.get(pk=int(location_id))
            except Exception:
                results.append({"index": idx, "success": False, "error": "invalid_location"})
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
            results.append({"index": idx, "success": False, "error": "integrity_error", "detail": str(e)})
            continue
        except Exception as e:
            results.append({"index": idx, "success": False, "error": "exception", "detail": str(e)})
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


@login_required
@permission_required("stock.view_stocklocation", raise_exception=True)
def search_locations(request: HttpRequest):
    if request.method != "GET":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    from stock.models import StockLocation

    locations = (
        StockLocation.objects.filter(name__icontains=query)
        .select_related("parent")
        .order_by("tree_id", "lft")[:50]
    )

    results = []
    for loc in locations:
        path = loc.pathstring if hasattr(loc, "pathstring") else loc.name
        results.append({"id": loc.pk, "text": path})

    return JsonResponse({"results": results})

