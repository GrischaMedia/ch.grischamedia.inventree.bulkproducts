from django.urls import path

from . import views

app_name = "bulkproducts"

urlpatterns = [
    path("", views.BulkProductsView.as_view(), name="index"),
    path("api/bulk-create/", views.bulk_create, name="api-bulk-create"),
]

