# Frontend ObRail

## Objectif

Le frontend ObRail est une interface de consultation pour un public institutionnel ou partenaire. Il expose les indicateurs principaux du dataset ferroviaire, l'etat de l'API et une liste filtrable de trajets sans imposer l'usage direct de Swagger.

## Stack

- Vite + React pour une application monopage simple.
- CSS natif dans `frontend/src/styles.css`.
- Service API centralise dans `frontend/src/services/api.js`.
- Tests unitaires Vitest pour les formatters et la construction des appels API.

## Configuration

Par defaut, le frontend appelle le backend sur :

```bash
http://localhost:8000
```

La variable `VITE_API_BASE_URL` permet de cibler une autre API :

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Parcours utilisateur

1. L'utilisateur arrive sur le tableau de bord et voit l'etat de sante de l'API.
2. Les indicateurs globaux affichent les volumes ferroviaires disponibles.
3. Les filtres permettent de reduire la liste par pays, type de train, gare de depart, gare d'arrivee et distance.
4. La pagination conserve une lecture stable des resultats par lots de 12 trajets.

## Etats geres

- Chargement des indicateurs et des trajets avec messages annonces aux technologies d'assistance.
- Erreur d'indicateurs separee de l'erreur de liste des trajets.
- Erreur reseau explicite lorsque le backend n'est pas joignable.
- Message vide lorsque les filtres ne retournent aucun trajet.
- Bouton de reinitialisation des filtres desactive si aucun filtre n'est actif.

## Accessibilite de base

Les points suivants ont ete renforces pour une base RGAA defendable :

- lien d'evitement vers la liste des trajets ;
- structure `main`, `header`, `section`, `nav` et titres hierarchises ;
- `aria-live` sur les statuts de sante, chargement et pagination ;
- `role="alert"` pour les erreurs ;
- focus visible sur champs, boutons et lien d'evitement ;
- libelles explicites sur les champs de filtres et boutons de pagination ;
- tableaux avec en-tetes `scope="col"`.

## Validation locale

Depuis `frontend/` :

```bash
npm install
npm run test
npm run build
```

Pour une validation manuelle :

```bash
npm run dev
```

Puis ouvrir `http://localhost:5173` et verifier :

- affichage correct avec backend disponible ;
- message clair si le backend est arrete ;
- navigation clavier dans les filtres, la pagination et le lien d'evitement ;
- absence de chevauchement sur mobile.
