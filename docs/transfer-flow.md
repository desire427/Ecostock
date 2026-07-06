# Flux métier — Transfert de produit

## Requête

```http
POST /api/products/{id}/move/
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "warehouse_id": 2
}
```

## Schéma de validation

```mermaid
flowchart TD
    A[POST /api/products/{id}/move/] --> B{Utilisateur authentifié ?}
    B -->|Non| C[401 Unauthorized]
    B -->|Oui| D[Récupérer le produit par ID]
    D --> E{Produit existe ?}
    E -->|Non| F[404 Not Found]
    E -->|Oui| G[Actualiser l'état via expiration_date]
    G --> H{Produit périmé ?}
    H -->|Oui| I[400 Bad Request<br/>Impossible de transférer un produit périmé]
    H -->|Non| J{warehouse_id valide ?}
    J -->|Non| K[400 Bad Request<br/>Entrepôt introuvable]
    J -->|Oui| L{Même entrepôt ?}
    L -->|Oui| M[400 Bad Request<br/>Déjà dans cet entrepôt]
    L -->|Non| N{Capacité disponible<br/>dans l'entrepôt cible ?}
    N -->|Non| O[400 Bad Request<br/>Capacité maximale atteinte]
    N -->|Oui| P[Mettre à jour product.warehouse]
    P --> Q[200 OK<br/>Produit transféré avec succès]
```

## Règles métier appliquées

1. **Authentification obligatoire** — Seuls les utilisateurs porteurs d'un JWT valide peuvent déclencher un transfert (`permission_classes = [IsAuthenticated]` sur l'action `move`).

2. **Interdiction de transfert périmé** — Un produit est considéré périmé si :
   - son état est `perime`, **ou**
   - sa `expiration_date` est antérieure à la date du jour.

3. **Capacité de l'entrepôt** — Chaque entrepôt possède une `capacity` maximale. Le nombre de produits stockés ne peut pas la dépasser.

4. **Entrepôt distinct** — Un transfert vers l'entrepôt actuel est rejeté.

## Exemple de réponses

### Succès (200)

```json
{
  "detail": "Produit transféré avec succès.",
  "product": {
    "id": 1,
    "name": "Pain complet",
    "quantity": 50,
    "expiration_date": "2026-07-10",
    "state": "disponible",
    "warehouse": 2,
    "warehouse_name": "Entrepôt Sud"
  },
  "from_warehouse": "Entrepôt Nord",
  "to_warehouse": "Entrepôt Sud"
}
```

### Échec — produit périmé (400)

```json
{
  "detail": "Impossible de transférer un produit périmé.",
  "state": "perime",
  "expiration_date": "2026-06-01"
}
```

### Échec — non authentifié (401)

```json
{
  "detail": "Informations d'authentification non fournies."
}
```

## Séquence temporelle

```
Client                API                     Base de données
  |                    |                            |
  |-- POST /move/ ---->|                            |
  |   + JWT            |-- SELECT product --------->|
  |                    |<-- product ----------------|
  |                    |-- Vérifications métier     |
  |                    |-- SELECT warehouse ------->|
  |                    |<-- warehouse --------------|
  |                    |-- UPDATE product.warehouse >|
  |                    |<-- OK ---------------------|
  |<-- 200 OK ---------|                            |
```
