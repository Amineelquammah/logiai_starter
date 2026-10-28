# Compte rendu : TP API LogiAI

**Noms :** "Saad Rakba - Amine El Quammah  **Groupe :**  5IIR G3

## 1. Environnement et premiers tests
- Environnement : Python 3.11, dépendances du projet installées dans `.venv`.
- Avant l'entraînement du modèle, `python -m pytest -q` donnait 5 échecs et 8 réussites : les tests qui ont besoin du modèle échouaient parce que `models/model.joblib` n'existait pas encore. Après `python -m logiai.train`, les 13 tests passent.
- Certains 422 sont automatiques : FastAPI valide le corps JSON à partir du modèle Pydantic. Les contraintes `Field`, les types et `Literal` refusent les valeurs invalides ; `extra="forbid"` refuse les champs inconnus.

## 2. Mon schéma
- Mes bornes et leur justification physique (une ligne par variable) :

| Variable | Min | Max | Pourquoi |
|---|---|---|---|
| distance_km | 1 | 1000 | Un trajet doit avoir une distance positive ; 1000 km couvre un long trajet routier. |
| poids_kg | > 0 | 3000 | Le colis doit peser quelque chose ; 3000 kg couvre la charge maximale représentée par le jeu de données. |
| heure_depart | 0 | 23 | Une heure du jour est un entier compris entre minuit et 23 h. |
| pluie_mm | 0 | 100 | La pluie ne peut pas être négative ; 100 mm représente une très forte précipitation. |
| trafic_index | 0 | 10 | L'indice est défini sur une échelle bornée de trafic fluide à saturé. |
| nb_arrets | 0 | 20 | Un nombre d'arrêts est entier et non négatif ; 20 couvre un itinéraire avec de nombreux arrêts. |

## 3. Ma fonction predict()
```python
def predict(livraison: Livraison):
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(status_code=503, detail="Le modèle de prédiction n'est pas chargé.")
    return PredictionOut(**predictor.predict(livraison.model_dump()))
```

## 4. Quatre requêtes
| Requête | Code obtenu | Pourquoi |
|---|---|---|
| livraison normale | 200 | Corps valide ; probabilité observée : 0,732, alerte : oui, seuil : 0,4. |
| distance_km = -5 | 422 | La distance doit être au moins égale à 1 km. |
| type_vehicule = "avion" | 422 | `Literal` n'autorise que `moto`, `fourgon` ou `camion`. |
| modèle absent (simulé en retirant le prédicteur de l'état) | 503 | Le service ne peut pas calculer de prédiction sans modèle. |

## 5. Questions de compréhension
1. On charge le modèle une seule fois au démarrage pour éviter de relire le fichier et de reconstruire le prédicteur à chaque requête, ce qui réduit la latence.
2. Pydantic vérifie cette borne, déclarée avec `Field(ge=0, le=100)` dans `logiai/api/schemas.py`. FastAPI renvoie automatiquement 422 si elle n'est pas respectée.
3. 422 signifie que la requête est invalide. 503 signifie que le service est temporairement incapable de répondre, ici parce que le modèle n'est pas chargé.
4. Le préfixe `/v1` identifie la version du contrat de l'API et permet de faire évoluer celui-ci sans casser les clients de la version précédente.
5. Une distance décimale valide, par exemple `12.5 km`, ne serait pas acceptée comme un entier par la validation Pydantic. `float` convient aux distances fractionnaires.

## 6. Décision : modèle absent
Le choix actuel est de démarrer l'API et de répondre 503 sur `/v1/predict` tant que le modèle est absent. Cela garde le service et son endpoint `/health` disponibles pour le diagnostic, mais les prédictions sont indisponibles. Refuser de démarrer signale immédiatement une configuration invalide et évite un service partiellement disponible, mais empêche aussi d'accéder à l'API pour diagnostiquer son état.

## 7. Lien de la pull request
À compléter après création de la branche `tp-api` et ouverture de la pull request. Aucun dépôt Git distant ni lien de pull request n'est configuré dans l'espace de travail actuel.
