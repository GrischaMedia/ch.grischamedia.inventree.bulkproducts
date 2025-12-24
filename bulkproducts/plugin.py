from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import NavigationMixin, SettingsMixin, UrlsMixin


class BulkProductsPlugin(UrlsMixin, NavigationMixin, SettingsMixin, InvenTreePlugin):
    """Bulk-create parts and optionally stock them in."""

    NAME = "Bulk Products"
    SLUG = "bulk-products"
    TITLE = _("Bulk Products")
    DESCRIPTION = _("Erstellt mehrere neue Teile in InvenTree und kann diese optional direkt einbuchen.")
    AUTHOR = "GrischaMedia.ch"
    PUBLISHED_DATE = "2025-12-24"
    VERSION = "1.1.11"
    WEBSITE = "https://github.com/grischamedia/ch.grischamedia.inventree.bulkproducts"
    LICENSE = "MIT"
    PUBLIC = True

    MIN_VERSION = "1.1.11"

    SETTINGS = {
        "ALLOW_CREATE": {
            "name": "Allow create",
            "description": "If enabled, the plugin is allowed to create records",
            "validator": bool,
            "default": True,
        },
        "DEFAULT_STOCK_LOCATION_ID": {
            "name": "Default stock location ID",
            "description": "Optional default location (database ID) for stock-in operations",
            "validator": int,
            "default": 0,
        },
    }

    NAVIGATION = [
        {
            "name": _("Massen hinzufügen"),
            "link": "plugin:bulk-products:index",
            "icon": "fa-plus",
            "roles": ["topbar", "sidebar"],
        }
    ]

    def setup_urls(self):
        from . import urls

        return urls.urlpatterns

