# Création du board Trello

Le board Trello est défini dans :

- `project/trello-board.md` pour lecture humaine ;
- `project/trello-board.csv` pour import ou automatisation ;
- `scripts/create_trello_board.py` pour création automatique via API Trello.

## Création automatique

Créer une clé/token Trello puis lancer :

```bash
export TRELLO_KEY="..."
export TRELLO_TOKEN="..."
python3 scripts/create_trello_board.py
```

Le script crée :

- le board `ObRail MSPR 3` ;
- les listes `Backlog`, `A faire`, `En cours`, `Review`, `Termine`, `Bloque` ;
- les cartes initiales à partir du CSV.

## Board créé

Board Trello : https://trello.com/b/V9sukZB6/obrail-mspr-3

## Création manuelle

Si l'API Trello n'est pas disponible, créer un board Trello nommé `ObRail MSPR 3`, puis recopier les listes et cartes depuis `project/trello-board.md`.
