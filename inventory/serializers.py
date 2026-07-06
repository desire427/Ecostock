from rest_framework import serializers

from .models import Product, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    nombre_produits = serializers.IntegerField(source="products.count", read_only=True)
    capacite_restante = serializers.IntegerField(read_only=True)

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


class ProductSerializer(serializers.ModelSerializer):
    nom_entrepot = serializers.CharField(source="warehouse.nom", read_only=True)
    state_display = serializers.CharField(source="get_state_display", read_only=True)
    est_perime = serializers.BooleanField(read_only=True)

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

    def validate_date_expiration(self, value):
        return value

    def validate(self, attrs):
        warehouse = attrs.get("warehouse", getattr(self.instance, "warehouse", None))
        if warehouse and warehouse.capacite_restante <= 0:
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
