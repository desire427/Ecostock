from django.db import models
from django.utils import timezone


class Warehouse(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom")
    localisation = models.CharField(max_length=255, verbose_name="Localisation")
    capacite = models.PositiveIntegerField(verbose_name="Capacité")

    class Meta:
        verbose_name = "Entrepôt"
        verbose_name_plural = "Entrepôts"
        ordering = ["nom"]

    def __str__(self):
        return self.nom

    @property
    def charge_actuelle(self):
        return self.products.count()

    @property
    def capacite_restante(self):
        return max(0, self.capacite - self.charge_actuelle)


class Product(models.Model):
    class State(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        RESERVE = "reserve", "Réservé"
        PERIME = "perime", "Périmé"

    nom = models.CharField(max_length=255, verbose_name="Nom")
    quantite = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    date_expiration = models.DateField(verbose_name="Date d'expiration")
    state = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.DISPONIBLE,
        verbose_name="État",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Entrepôt",
    )

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["date_expiration", "nom"]

    def __str__(self):
        return f"{self.nom} ({self.get_state_display()})"

    @property
    def est_perime(self):
        return (
            self.state == self.State.PERIME
            or self.date_expiration < timezone.localdate()
        )

    def actualiser_etat(self):
        if self.date_expiration < timezone.localdate():
            self.state = self.State.PERIME
        return self.state
