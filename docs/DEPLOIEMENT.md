> Pour le déploiement persistant Gunicorn/Docker avec sauvegardes et Cloudflare, suivez [CLOUDFLARE.md](CLOUDFLARE.md). Les commandes `python server.py` ci-dessous sont réservées au développement. L’inscription publique est désormais désactivée par défaut.

# Exécution et sauvegardes

## Développement ou pilote privé

```bash
./scripts/install.sh
HOST=127.0.0.1 PORT=3000 .venv/bin/python server.py
```

Fournissez Python 3.12+, un volume persistant pour `.data`, et un superviseur qui relance le processus. Ne placez pas le volume de base de données dans un répertoire servi par HTTP. Le serveur intégré n’est pas destiné à l’exposition directe sur Internet.

Variables reconnues :

| Variable | Valeur / fonction |
|---|---|
| `HOST` | `0.0.0.0` par défaut ; préférer `127.0.0.1` derrière un proxy local |
| `PORT` | `3000` |
| `BAZAR_DB` | Chemin de base, défaut `.data/bazar.sqlite3` |
| `COOKIE_SECURE` | `1` pour des sessions transmises uniquement sur HTTPS |
| `SMTP_HOST`, `SMTP_PORT` | Messagerie sortante STARTTLS, port 587 par défaut |
| `SMTP_FROM` | Adresse émettrice autorisée |
| `SMTP_USER`, `SMTP_PASSWORD` | Authentification SMTP si requise |

Placez les secrets dans le gestionnaire de secrets de l’hébergeur. Le programme lit les variables de processus et ne charge pas automatiquement un fichier `.env`. Le mode SMTP STARTTLS vérifie le certificat ; aucune option de désactivation TLS n’est prévue. La livraison réelle doit être testée avec le fournisseur choisi. Les appels SMTP sont synchrones ; une file et des identifiants de livraison sont nécessaires avant envois à grande échelle.

Pour une exposition pilote, configurez un reverse proxy HTTPS (Caddy/Nginx), `COOKIE_SECURE=1`, une limite de corps de 2 Mo et une limitation de débit sur `/api/login` et `/api/register`. Confirmez les droits d’inscription avant ouverture publique. Une analyse et un renforcement de production restent requis ; cette documentation ne constitue pas une validation de sécurité d’un SaaS public.

## Sauvegarde cohérente

```bash
.venv/bin/python scripts/backup.py --destination /chemin/prive/sauvegardes
```

La commande utilise l’API SQLite Backup et vérifie l’intégrité. Elle fonctionne avec une application active. Les sauvegardes contiennent des données personnelles et hashes de comptes : protégez-les, chiffrez leur copie externe et limitez l’accès. Planifiez cette commande quotidiennement via votre ordonnanceur, avec rétention définie par l’entreprise. Aucune tâche récurrente n’est installée automatiquement.

Restauration : arrêtez le serveur, conservez une copie de la base actuelle, restaurez la sauvegarde dans `BAZAR_DB`, protégez ses droits et redémarrez. Une sauvegarde peut contenir des sessions : invalidez-les après restauration avec `DELETE FROM sessions` depuis SQLite. Vérifiez ensuite la connexion, les boutiques, les quantités et une facture. Testez régulièrement la restauration sur un environnement séparé.

## Contrôles de disponibilité

`GET /` doit retourner 200 et la page de connexion. `GET /api/state` sans cookie doit retourner 401. Une disponibilité fonctionnelle exige en plus un parcours authentifié : ajout d’article, vente, paiement et facture. Les tests automatisés utilisent une base temporaire et ne modifient pas les données réelles.
