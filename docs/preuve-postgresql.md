# Preuve de la base PostgreSQL

Cette page sert de preuve simple pour montrer que le projet utilise bien une base PostgreSQL et que les trajets sont importes dans une table applicative.

## Demarrer la stack

Depuis la racine du depot :

```bash
docker compose -f docker/docker-compose.yml up --build
```

Le backend attend le service PostgreSQL `db`, lance `python seed.py`, puis demarre l'API.

## Lancer la preuve

Dans un autre terminal :

```bash
bash scripts/preuve_postgresql.sh
```

Le script affiche :

- le conteneur PostgreSQL `docker-db-1` ;
- la base `obrail` ;
- la table `public.trips` ;
- le nombre de trajets importes ;
- quelques lignes issues de la table.

## Sortie observee localement

Apres le seed du 23/06/2026 :

```text
Tables de la base obrail
        List of relations
 Schema | Name  | Type  | Owner
--------+-------+-------+--------
 public | trips | table | obrail
(1 row)

Nombre de trajets importes
 nombre_de_trajets
-------------------
            142411
(1 row)
```

La preuve montre donc :

- PostgreSQL tourne dans Docker ;
- la base `obrail` existe ;
- la table `trips` existe ;
- les donnees ferroviaires sont bien chargees en base.
