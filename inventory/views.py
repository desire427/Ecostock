from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Product, Warehouse
from .serializers import (
    ProduitDeplacerSerializer,
    ProductSerializer,
    WarehouseSerializer,
)


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.annotate(product_count=Count("products"))
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["get"])
    def audit(self, request, pk=None):
        warehouse = self.get_object()
        aggregates = warehouse.products.aggregate(
            total_produits=Count("id"),
            quantite_totale=Sum("quantite"),
        )
        by_state = (
            warehouse.products.values("state")
            .annotate(count=Count("id"))
            .order_by("state")
        )
        
        return Response(
            {
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.nom,
                "capacity": warehouse.capacite,
                "total_products": aggregates["total_produits"] or 0,
                "total_quantity": aggregates["quantite_totale"] or 0,
                "remaining_capacity": max(0, warehouse.capacite - warehouse.products.count()),
                "by_state": {
                    item["state"]: item["count"] for item in by_state
                },
            }
        )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("warehouse")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def _actualiser_etat_si_perime(self, produit):
        """Met à jour l'état du produit s'il est périmé."""
        if produit.date_expiration < timezone.localdate() and produit.state != Product.State.PERIME:
            produit.state = Product.State.PERIME
            produit.save(update_fields=["state"])

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def deplacer(self, request, pk=None):
        product = self.get_object()
        self._actualiser_etat_si_perime(product)
        est_perime = (product.state == Product.State.PERIME or 
                      product.date_expiration < timezone.localdate())
        if est_perime:
            return Response(
                {
                    "detail": "Impossible de transférer un produit périmé.",
                    "state": product.state,
                    "expiration_date": product.date_expiration,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProduitDeplacerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        warehouse_id_cible = serializer.validated_data["warehouse_id"]

        if warehouse_id_cible == product.warehouse_id:
            return Response(
                {"detail": "Le produit est déjà dans cet entrepôt."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # On utilise select_for_update pour verrouiller la ligne de l'entrepôt
                # et éviter les "race conditions" sur le calcul de la capacité.
                entrepot_cible = Warehouse.objects.select_for_update().get(pk=warehouse_id_cible)

                # La logique de 'capacite_restante' est maintenant ici
                capacite_restante_cible = entrepot_cible.capacite - entrepot_cible.products.count()
                if capacite_restante_cible <= 0:
                    return Response(
                        {"detail": "L'entrepôt de destination a atteint sa capacité maximale."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                entrepot_source = product.warehouse
                product.warehouse = entrepot_cible
                product.save(update_fields=["warehouse"])
        except Warehouse.DoesNotExist:
            # Cette erreur est déjà gérée par le serializer, mais c'est une bonne pratique.
            return Response({"detail": "Entrepôt introuvable."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "detail": "Produit transféré avec succès.",
                "product": ProductSerializer(product).data,
                "from_warehouse": entrepot_source.nom,
                "to_warehouse": entrepot_cible.nom,
            },
            status=status.HTTP_200_OK,
        )
