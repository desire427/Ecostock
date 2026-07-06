from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, WarehouseViewSet

router = DefaultRouter()
router.register(r"entrepots", WarehouseViewSet, basename="entrepot")
router.register(r"produits", ProductViewSet, basename="produit")

urlpatterns = [
    path("", include(router.urls)),
]
