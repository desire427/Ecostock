from django.utils import timezone
from rest_framework import serializers

from .models import Product, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    nombre_produits = serializers.IntegerField(read_only=True)
    capacite_restante = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "nom",
            "localisation",
            "capacite",
            "nombre_produits",
            "capacite_restante",
        ]
    
    def get_nombre_produits(self, obj):
        # 'obj' est une instance de Warehouse
        return obj.products.count()

    def get_capacite_restante(self, obj):
        return max(0, obj.capacite - obj.products.count())


class ProductSerializer(serializers.ModelSerializer):
    nom_entrepot = serializers.CharField(source="warehouse.nom", read_only=True)
    state_display = serializers.CharField(source="get_state_display", read_only=True)
    est_perime = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "nom",
            "quantite",
            "date_expiration",
            "state",
            "state_display",
            "est_perime",
            "warehouse",
            "nom_entrepot",
        ]
        read_only_fields = ["state"]
    
    def get_est_perime(self, obj):
        # 'obj' est une instance de Product
        return obj.state == Product.State.PERIME or obj.date_expiration < timezone.localdate()

    def validate_date_expiration(self, value):
        # On s'assure que l'état est correct dès la validation
        if value < timezone.localdate():
            self.initial_data['state'] = Product.State.PERIME
        return value

    def validate(self, attrs):
        """Vérifie la capacité de l'entrepôt lors de la création/modification."""
        warehouse = attrs.get("warehouse", getattr(self.instance, "warehouse", None))
        
        if warehouse and (warehouse.capacite - warehouse.products.count()) <= 0:
            if self.instance is None or self.instance.warehouse_id != warehouse.id:
                raise serializers.ValidationError(
                    {"warehouse": "L'entrepôt a atteint sa capacité maximale."}
                )
        return attrs


class ProduitDeplacerSerializer(serializers.Serializer):
    warehouse_id = serializers.IntegerField()

    def validate_warehouse_id(self, value):
        if not Warehouse.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Entrepôt introuvable.")
        return value
