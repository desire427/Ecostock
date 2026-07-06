# Eco-Stock API

API REST Django pour la gestion de stocks alimentaires de la startup **Eco-Stock**.

## Prérequis

- Python 3.11+
- pip

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Authentification JWT

Seuls les utilisateurs authentifiés peuvent **modifier** le stock (création, mise à jour, suppression, transfert).

```bash
# Obtenir un token
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "votre_mot_de_passe"}'

# Utiliser le token
curl -H "Authorization: Bearer <access_token>" \
  http://127.0.0.1:8000/api/products/
```

## Documentation interactive

- Schéma OpenAPI : `GET /api/schema/`
- Swagger UI : `GET /api/docs/`

## Modèle de données

| Modèle     | Champs                                                                 |
|------------|------------------------------------------------------------------------|
| Warehouse  | nom, localisation, capacité                                            |
| Product    | nom, quantité, date d'expiration, état, entrepôt (FK)                  |
| États      | `disponible`, `reserve`, `perime`                                      |

Relation : **1 entrepôt → N produits**

## Endpoints (OpenAPI)

```yaml
openapi: 3.0.3
info:
  title: Eco-Stock API
  version: 1.0.0
  description: Gestion de stocks alimentaires

servers:
  - url: http://127.0.0.1:8000

paths:
  /api/token/:
    post:
      summary: Obtenir un token JWT
      tags: [Auth]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [username, password]
              properties:
                username: { type: string }
                password: { type: string, format: password }
      responses:
        '200':
          description: Tokens JWT
          content:
            application/json:
              schema:
                type: object
                properties:
                  access: { type: string }
                  refresh: { type: string }

  /api/token/refresh/:
    post:
      summary: Rafraîchir le token d'accès
      tags: [Auth]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [refresh]
              properties:
                refresh: { type: string }
      responses:
        '200':
          description: Nouveau token d'accès

  /api/warehouses/:
    get:
      summary: Lister les entrepôts
      tags: [Warehouses]
      responses:
        '200':
          description: Liste des entrepôts
    post:
      summary: Créer un entrepôt
      tags: [Warehouses]
      security: [{ bearerAuth: [] }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WarehouseInput'
      responses:
        '201': { description: Entrepôt créé }
        '401': { description: Non authentifié }

  /api/warehouses/{id}/:
    get:
      summary: Détail d'un entrepôt
      tags: [Warehouses]
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: integer }
      responses:
        '200': { description: Détail entrepôt }
        '404': { description: Introuvable }
    put:
      summary: Mettre à jour un entrepôt
      tags: [Warehouses]
      security: [{ bearerAuth: [] }]
      responses:
        '200': { description: Entrepôt mis à jour }
        '401': { description: Non authentifié }
    patch:
      summary: Mise à jour partielle
      tags: [Warehouses]
      security: [{ bearerAuth: [] }]
      responses:
        '200': { description: Entrepôt mis à jour }
    delete:
      summary: Supprimer un entrepôt
      tags: [Warehouses]
      security: [{ bearerAuth: [] }]
      responses:
        '204': { description: Supprimé }

  /api/warehouses/{id}/audit/:
    get:
      summary: Audit d'un entrepôt
      description: Retourne le nombre total de produits et les agrégations par état.
      tags: [Warehouses]
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: integer }
      responses:
        '200':
          description: Rapport d'audit
          content:
            application/json:
              schema:
                type: object
                properties:
                  warehouse_id: { type: integer }
                  warehouse_name: { type: string }
                  capacity: { type: integer }
                  total_products: { type: integer }
                  total_quantity: { type: integer }
                  remaining_capacity: { type: integer }
                  by_state:
                    type: object
                    additionalProperties: { type: integer }

  /api/products/:
    get:
      summary: Lister les produits
      tags: [Products]
      responses:
        '200': { description: Liste des produits }
    post:
      summary: Créer un produit
      tags: [Products]
      security: [{ bearerAuth: [] }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProductInput'
      responses:
        '201': { description: Produit créé }
        '400': { description: Données invalides }
        '401': { description: Non authentifié }

  /api/products/{id}/:
    get:
      summary: Détail d'un produit
      tags: [Products]
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: integer }
      responses:
        '200': { description: Détail produit }
    put:
      summary: Mettre à jour un produit
      tags: [Products]
      security: [{ bearerAuth: [] }]
      responses:
        '200': { description: Produit mis à jour }
        '401': { description: Non authentifié }
    patch:
      summary: Mise à jour partielle
      tags: [Products]
      security: [{ bearerAuth: [] }]
      responses:
        '200': { description: Produit mis à jour }
    delete:
      summary: Supprimer un produit
      tags: [Products]
      security: [{ bearerAuth: [] }]
      responses:
        '204': { description: Supprimé }

  /api/products/{id}/move/:
    post:
      summary: Transférer un produit vers un autre entrepôt
      description: |
        Transfère un produit si et seulement si :
        - l'utilisateur est authentifié
        - le produit n'est pas périmé
        - l'entrepôt de destination a de la capacité disponible
        - l'entrepôt de destination est différent de l'actuel
      tags: [Products]
      security: [{ bearerAuth: [] }]
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: integer }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [warehouse_id]
              properties:
                warehouse_id: { type: integer }
      responses:
        '200': { description: Transfert réussi }
        '400': { description: Produit périmé ou règle métier violée }
        '401': { description: Non authentifié }
        '404': { description: Produit ou entrepôt introuvable }

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    WarehouseInput:
      type: object
      required: [name, location, capacity]
      properties:
        name: { type: string, example: "Entrepôt Nord" }
        location: { type: string, example: "Paris 18e" }
        capacity: { type: integer, minimum: 1, example: 100 }

    ProductInput:
      type: object
      required: [name, quantity, expiration_date, warehouse]
      properties:
        name: { type: string, example: "Pain complet" }
        quantity: { type: integer, minimum: 1, example: 50 }
        expiration_date: { type: string, format: date, example: "2026-07-10" }
        warehouse: { type: integer, example: 1 }
```

## Flux métier — Transfert de produit

Voir le schéma détaillé dans [`docs/transfer-flow.md`](docs/transfer-flow.md).

## Structure du projet

```
EcoStock/
├── ecostock/          # Configuration Django
├── inventory/         # App métier (modèles, vues, serializers)
├── docs/              # Schémas et documentation
├── requirements.txt
└── manage.py
```

## Codes HTTP utilisés

| Code | Usage                                      |
|------|--------------------------------------------|
| 200  | Succès (lecture, transfert)                |
| 201  | Ressource créée                            |
| 204  | Ressource supprimée                        |
| 400  | Validation métier ou données invalides     |
| 401  | Authentification requise                   |
| 404  | Ressource introuvable                      |
