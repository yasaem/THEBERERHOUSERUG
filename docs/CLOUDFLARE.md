# Déploiement persistant avec Cloudflare Tunnel

Architecture préparée : **client HTTPS → Cloudflare → tunnel sortant → Gunicorn / application Docker → volume SQLite persistant**. Le service de sauvegarde réalise une copie cohérente toutes les six heures dans un volume distinct.

Cloudflare n’héberge pas, à lui seul, le serveur Python et son disque SQLite. Ce projet n’est pas un Worker/D1 : il faut un VPS Linux ou un serveur Docker qui reste allumé. Un PC personnel peut être utilisé pour une démonstration, mais son extinction couperait l’application ; il n’est pas retenu comme hébergement commercial.

## Prérequis externes

- Compte Cloudflare accessible et domaine que vous contrôlez dans ce compte.
- Serveur Linux persistant, Docker Engine et Docker Compose, accès administrateur/SSH.
- Nom HTTPS à utiliser, par exemple `erp.votre-domaine.ma`.
- Fournisseur de messagerie si vous souhaitez envoyer des factures.

L’autorisation donnée dans le chat ne fournit pas un accès à votre PC, au compte Cloudflare ou à un serveur. Aucun hébergement payant ni domaine n’a été acheté. Aucun secret réel n’est inclus dans le dépôt.

## Installer sur le serveur

```bash
git clone https://github.com/yasaem/THEBERERHOUSERUG.git
cd THEBERERHOUSERUG
cp deploy.env.example .env
chmod 600 .env
```

Renseignez `PUBLIC_BASE_URL` avec le domaine HTTPS réel. Configurez éventuellement SMTP dans ce fichier privé ou dans le gestionnaire de secrets de votre hébergeur. Ne copiez pas les valeurs dans un ticket, une capture publique ou le chat.

```bash
docker compose build
docker compose up -d app backup
docker compose exec app python scripts/create_platform_admin.py
```

Les mots de passe sont saisis dans le terminal, pas comme arguments de commande. L’inscription publique est désactivée et les cookies sont Secure. Ne désactivez pas ce réglage pour un déploiement public.

## Connecter Cloudflare

Depuis votre compte Cloudflare, créez un tunnel **géré à distance** et récupérez le jeton du connecteur Docker. Les libellés du tableau de bord Cloudflare peuvent évoluer.

1. Stockez ce jeton dans `CLOUDFLARE_TUNNEL_TOKEN` du fichier `.env` privé du serveur.
2. Configurez le nom public correspondant à `PUBLIC_BASE_URL`.
3. Pour ce nom, configurez le service du tunnel : **HTTP, `http://app:3000`**. `app` est le service Docker, pas `localhost` du conteneur cloudflared.
4. Lancez le connecteur :

```bash
docker compose --profile cloudflare up -d
```

Le connecteur officiel est épinglé par son digest vérifié dans `compose.yaml`. Son binaire a été exécuté dans les tests, mais la connexion à votre compte n’a pas été vérifiée sans jeton réel.

L’application n’est publiée qu’en boucle locale sur le serveur ; le tunnel utilise le réseau Docker. N’ouvrez pas directement le port 3000 sur Internet. Activez la redirection HTTP vers HTTPS dans Cloudflare et configurez les règles de protection/limitation de débit adaptées. Ne cachez pas `/api/*` ni les réponses authentifiées. Le contrôle métier d’accès ne doit pas être remplacé par des règles DNS.

## Vérifier après publication

- Le domaine HTTPS affiche la page de connexion en français et anglais.
- L’inscription libre est absente et `/api/public-config` annonce `allow_signup: false`.
- Connexion éditeur, création d’un client, remplacement du mot de passe provisoire, ajout d’une sous-boutique, vente et PDF.
- Renouvellement, suspension et blocage effectif d’une session déjà ouverte.
- `docker compose ps` annonce les services attendus ; `/healthz` retourne 200.
- Les données restent présentes après un redémarrage du conteneur `app`.

Une vérification locale du conteneur ne prouve pas la disponibilité de votre domaine public. La publication n’est pas déclarée réussie tant que les accès Cloudflare et serveur n’ont pas permis ce test réel.

## Sauvegardes et mises à jour

Le service `backup` utilise le même utilisateur non privilégié que l’application et produit des fichiers de mode 0600. Les sauvegardes locales protègent contre une erreur applicative ; elles ne protègent pas contre la perte du serveur. Configurez une copie externe chiffrée, une rétention et des tests périodiques de restauration avant exploitation commerciale.

Ne lancez pas `docker compose down -v` : cela supprimerait les volumes. Avant une mise à jour, effectuez une sauvegarde et conservez l’image précédente. Les migrations de cette version sont additives et idempotentes, mais un retour de version avec une base modifiée doit être vérifié séparément.

```bash
docker compose exec app python scripts/backup.py --destination /data/pre-upgrade-backups
git pull --ff-only
docker compose build
docker compose --profile cloudflare up -d
```

Pour restaurer : arrêtez les services `app` et `backup`, archivez la base actuelle et ses éventuels fichiers `-wal` / `-shm`, installez une sauvegarde vérifiée à l’emplacement attendu avec les droits UID/GID 10001, invalidez les sessions restaurées puis redémarrez. Ne remplacez jamais un fichier SQLite sous un serveur actif. La restauration dans une base séparée a été testée avec des données fictives.

## Construction sans DNS dans Docker

Le premier build dans l’environnement Codex a rencontré un DNS indisponible à l’intérieur de Docker. La correction testée conserve TLS et les vérifications de téléchargement de pip : téléchargement des roues depuis le runtime connecté, puis installation hors réseau dans l’image.

```bash
.venv/bin/python -m pip download --only-binary=:all: --dest .build/wheels -r requirements.txt
docker build --build-arg DEPENDENCY_STAGE=offline -t bazar-erp:local .
```

Les roues doivent correspondre à Python 3.12 et à la plateforme cible. Elles sont exclues de Git. La construction standard utilise toujours PyPI en HTTPS.

## Limites de capacité

SQLite WAL permet un serveur persistant et plusieurs travailleurs Gunicorn, avec sérialisation des écritures. Ce déploiement est mono-serveur : ne répliquez pas plusieurs instances sur des disques indépendants et n’exposez pas le volume sur un système de fichiers réseau. Aucune capacité commerciale chiffrée n’est garantie sans test de charge. PostgreSQL, stockage externe des documents, file d’envoi d’e-mails, supervision et reprise sur incident restent nécessaires pour une offre à plus grande échelle.
