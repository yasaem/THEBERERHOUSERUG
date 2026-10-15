# Bazar — ERP de commerce

**Français** · [English documentation](README_EN.md)

Application web bilingue français / anglais pour les commerces marocains. Interface responsive, API Python, SQLite, PDF ReportLab. Cette version ajoute l’espace éditeur SaaS, la création des entreprises clientes, les formules et les règlements manuels. Le déploiement public et le paiement automatique nécessitent encore vos accès externes et une recette de production.

## Ouvrir une version web sans domaine ni VPS

[**Déployer l’aperçu gratuit sur Render**](https://render.com/deploy?repo=https://github.com/yasaem/THEBERERHOUSERUG)

Render fournit une adresse HTTPS automatiquement. Connectez votre compte GitHub à Render si nécessaire et renseignez votre e-mail et votre mot de passe éditeur dans les champs sécurisés. Aucun mot de passe n’est à transmettre dans le chat. Vérifiez le plan Free avant de lancer. [Instructions de l’aperçu](docs/RENDER_PREVIEW.md).

**Données temporaires : cet aperçu gratuit n’est pas destiné aux données réelles ou à une exploitation commerciale.** Il peut être mis en veille et perdre son disque SQLite. Le déploiement et son URL ne sont pas encore créés ; le lien ci-dessus ouvre le formulaire de déploiement.

## Récupérer le code

```bash
git clone https://github.com/yasaem/THEBERERHOUSERUG.git
cd THEBERERHOUSERUG
```

Si le dépôt est déjà présent, utilisez ce dossier et préservez les changements locaux avant une mise à jour.

## Démarrer

Python 3.12 ou supérieur.

```bash
./scripts/install.sh
.venv/bin/python server.py
```

Le serveur de développement écoute sur le port **3000** (`PORT` et `HOST` configurables). **L’inscription publique est fermée par défaut.** Créez d’abord votre compte éditeur avec la commande ci-dessous, connectez-vous puis créez les comptes de vos clients depuis cet espace. Aucun compte ni mot de passe par défaut n’est installé. La base locale `.data/bazar.sqlite3` est créée automatiquement et exclue de Git.

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check static/app.js
```

## Exploitation SaaS et compte éditeur

```bash
.venv/bin/python scripts/create_platform_admin.py
```

La saisie du mot de passe est masquée. L’éditeur crée chaque entreprise, son administrateur et sa première boutique. Le client remplace son mot de passe provisoire puis gère ses boutiques et utilisateurs. Les droits, quotas et l’état de l’abonnement sont vérifiés par le serveur sur chaque requête.

Créez vos formules (prix mensuel MAD, limites de boutiques et d’utilisateurs), enregistrez les virements/espèces reçus et renouvelez la période. Vous pouvez suspendre ou réactiver un accès en conservant les données. Aucun débit bancaire automatique n’est effectué. Les nouvelles entreprises ont un essai de 14 jours ; redémarrer l’application ne le prolonge pas.

- [Guide éditeur et abonnements](docs/SAAS.md)
- [Déploiement Docker et Cloudflare](docs/CLOUDFLARE.md)

Pour un hébergement persistant :

```bash
cp deploy.env.example .env
chmod 600 .env
# Renseigner le domaine HTTPS et les secrets dans .env, sans les publier.
docker compose build
docker compose up -d app backup
docker compose exec app python scripts/create_platform_admin.py
# Après configuration du tunnel Cloudflare dans .env :
docker compose --profile cloudflare up -d
```

Gunicorn sert l’application, le disque SQLite est conservé dans un volume et un second service réalise une sauvegarde toutes les six heures. Le tunnel nécessite un compte Cloudflare, un domaine et un serveur qui reste allumé. La mise en ligne externe n’est pas encore réalisée faute d’accès fournis. Ne supprimez pas les volumes avec `docker compose down -v`.

Pour un test local sans Docker :

```bash
.venv/bin/gunicorn --config gunicorn.conf.py wsgi:application
```

`python server.py` reste disponible pour le développement. Le drapeau `BAZAR_ALLOW_SIGNUP=1` existe uniquement pour les démonstrations et les tests ; ne l’activez pas sur votre service commercial.

## Choisir français ou anglais

Le sélecteur **Français / English** est disponible avant la connexion et dans la barre supérieure de toutes les pages. Le choix est conservé dans ce navigateur, y compris après rechargement et déconnexion. Il concerne menus, formulaires, messages, tableaux, états et en-têtes CSV. Les noms de produits, clients, boutiques et les autres données saisies ne sont jamais traduits automatiquement.

Ouvrez une facture puis choisissez sa **langue de facture**, indépendamment de celle de l’interface. L’aperçu, l’impression, le PDF téléchargé, le sujet et le corps de l’e-mail utilisent ce choix. Les montants historiques, taux, références et identifiants ne sont pas modifiés. La langue ne change pas la devise : les montants restent en MAD.

Les traductions d’interface sont dans `static/translations.json`, le moteur dans `static/i18n.js`, et les libellés PDF dans `documents.py`. Le serveur traduit les erreurs selon `X-App-Language`; les routes de documents acceptent `language: "fr"` ou `"en"` (français par défaut, langue non supportée refusée).

## Parcours disponible

- Comptes clients créés par l’éditeur, connexion, sessions HttpOnly/SameSite et protection CSRF.
- Entreprises isolées, boutiques et comptes avec quatre rôles. Affectation à une boutique pour les comptes non propriétaires.
- Catalogue personnalisable, modification, archivage, ajustements justifiés et journal des mouvements.
- Import CSV UTF-8 / Excel `.xlsx` avec association des colonnes, aperçu, validation atomique et refus des références en doublon. Exemple : [docs/stock-exemple.csv](docs/stock-exemple.csv).
- Ventes multi-articles, articles libres, remise, TVA, shipping, frais bancaires et paiement initial partiel.
- Commissions multiples, enveloppe vendeurs répartie en pourcentage, taux ou montant fixe, arrondis conservant l’enveloppe au centime.
- Règlements partiels distincts pour ventes, commissions, dépenses et salaires.
- Annulation tracée avec restauration unique du stock et neutralisation des commissions non réglées.
- Clients, partenaires, employés, salaires déclarés, dépenses, tableaux de bord mensuels et export CSV.
- Factures A4 : impression, téléchargement PDF, logo et mentions d’entreprise, instantané immuable des lignes et de l’émetteur.
- Envoi SMTP d’un PDF lorsque le service est configuré (non vérifié avec un fournisseur externe).
- Gestion des comptes : activation, désactivation, rôle, boutique, réinitialisation du mot de passe et révocation des sessions.

## Règles retenues pour la recette

Tous les montants sont en **MAD**, stockés en centimes entiers. Les prix saisis sont **HT**. Remise globale en montant HT ; une TVA de 0, 10 ou 20 % s’applique après remise. La base des commissions est `max(0, HT après remise − shipping supporté)`, sans TVA ni déduction des frais bancaires. Le shipping saisi est une charge supportée, pas une livraison facturée au client.

Les vendeurs partagent une enveloppe unique (même taux ou même montant fixe), selon des parts totalisant 100 %. Les autres intervenants ont des commissions indépendantes. L’arrondi est commercial au centime ; la répartition vendeur utilise les plus forts restes pour ne pas créer ou perdre de centime.

Le résultat de gestion retranche les coûts historiques, shipping, banque, commissions acquises, dépenses et salaires dus. Les règlements ne sont pas une seconde charge. N’enregistrez pas à nouveau en dépenses les frais déjà saisis sur une vente ou les salaires déjà déclarés. Les coûts inconnus des articles libres sont considérés comme zéro : la contribution estimée doit être interprétée en conséquence.

Une annulation conserve les encaissements dans l’historique. Leur remboursement doit être traité séparément ; il n’existe pas encore de flux de remboursement automatisé. Une commission déjà payée bloque l’annulation pour éviter une perte de traçabilité financière.

## Limites par rapport au cahier des charges

Voir [la couverture et les points restant à réaliser](docs/RECETTE.md). Les devises EUR/USD et taux de change, permissions personnalisées, affectations multiples de boutiques, retours partiels/avoirs, livraison facturée, taxes configurables, numérotation légale, paiements automatiques d’abonnement et transferts ne sont pas réalisés. Les listes sont chargées intégralement ; la pagination serveur et la validation de charge restent à développer.

Avant une mise en production commerciale : validation fiscale marocaine, recette utilisateur, contrôle de sécurité, infrastructure HTTPS, sauvegardes externes, envoi SMTP et architecture de déploiement adaptée. Le serveur HTTP intégré est réservé au développement ; Gunicorn et Docker sont préparés et testés pour le serveur persistant, sans garantie de charge chiffrée.

## Documentation

- [Guide utilisateur](docs/GUIDE.md)
- [Architecture et modèle relationnel](docs/ARCHITECTURE.md)
- [Déploiement et sauvegardes](docs/DEPLOIEMENT.md)
- [Couverture, recette et limites](docs/RECETTE.md)

## Sauvegarder, envoyer les factures et déployer

```bash
.venv/bin/python scripts/backup.py --destination /chemin/prive/sauvegardes
```

La sauvegarde est vérifiée par SQLite. Prévoyez une copie externe protégée et un test de restauration. La planification des sauvegardes n’est pas installée automatiquement.

Pour l’e-mail, configurez `SMTP_HOST`, `SMTP_PORT` (587 par défaut), `SMTP_FROM` et, si nécessaire, `SMTP_USER` / `SMTP_PASSWORD` dans le gestionnaire de secrets de l’hébergeur. STARTTLS est obligatoire et le certificat est vérifié. L’envoi réel dépend du fournisseur ; les tests de composition FR/EN utilisent un SMTP simulé et n’envoient aucun message externe.

Pour un pilote derrière un reverse proxy HTTPS : `HOST=127.0.0.1`, `PORT=3000`, `COOKIE_SECURE=1` et volume persistant pour `BAZAR_DB`. Le serveur fourni reste un serveur de développement : voir [les procédures et limites de déploiement](docs/DEPLOIEMENT.md) avant une ouverture publique.

Ne versionnez jamais `.data/`, `.venv/`, `.env`, sauvegardes ou identifiants SMTP ; ces éléments sont exclus par `.gitignore`. Le code et la documentation sont destinés à la branche `main` du dépôt GitHub ci-dessus.

## Validation de cette évolution

40 tests ont été exécutés avec succès, y compris dans le conteneur. Le parcours éditeur/client, les quotas, les paiements, la suspension et le changement obligatoire du mot de passe ont aussi été vérifiés dans Chromium. Le redémarrage d’un conteneur avec volume, une sauvegarde et sa restauration dans une base séparée ont été contrôlés. Le connecteur Cloudflare officiel a été téléchargé avec vérification de digest et exécuté (`--version`), mais aucun tunnel de production n’a été connecté.

Le workflow GitHub Actions vérifie les tests et la syntaxe JavaScript sur chaque push/PR ; sa présence ne signifie pas qu’une exécution distante a déjà été observée.

### Ventes, logo, messagerie et paie

- **Ventes** : les frais bancaires peuvent être saisis en MAD ou en pourcentage du **total TTC**. La part de répartition apparaît uniquement pour un vendeur ; les guides et agences ont leur propre commission.
- **Paramètres → Entreprise & logo** : téléverser un PNG/JPEG (500 Ko maximum). Les nouvelles factures et les nouveaux bulletins conservent les informations de l’entreprise ; les documents historiques ne sont pas modifiés.
- **Employés & salaires** : préparer les salaires du mois en une opération, sans doublons. Les règlements restent explicites. La fiche de gestion permet des primes et retenues avant paiement.
- **Paie marocaine** : renseigner CIN/CNSS/personnes à charge, puis configurer et valider le barème de l’année (propriétaire uniquement). Cocher « Bulletin marocain » à la préparation. Le salaire de référence est alors **brut**. Le moteur calcule CNSS salarié plafonnée, AMO, frais professionnels, IR annualisé et déductions familiales. Les paramètres et identités sont figés dans le PDF FR/EN. La référence indicative fournie est celle de **2025**, non une certification des règles 2026. Une validation comptable est nécessaire pour l’année utilisée. Cas particuliers, charges patronales, déclarations CNSS, congés, heures supplémentaires, primes exonérées et régularisation annuelle ne sont pas automatisés. Un bulletin marocain généré est figé ; ne pas utiliser le réglage de primes de la fiche simple pour le modifier.
- Les anciens salaires restent conservés ; ils ne sont pas convertis rétroactivement en bulletins marocains. La préparation mensuelle est déclenchée par un bouton, sans virement ni tâche planifiée garantie sur Render gratuit.

### Activer simplement les e-mails sur Render

Utiliser Resend via HTTPS : créer un compte sur <https://resend.com>, vérifier une adresse/domaine expéditeur autorisé, puis ajouter dans **Render → Environment** les secrets `RESEND_API_KEY` et `MAIL_FROM` (ex. `Bazar <factures@votre-domaine.fr>`). Redéployer. La clé reste côté serveur et n’est jamais envoyée au navigateur. Aucun mot de passe ou clé ne doit être ajouté au dépôt ou au chat.

Sans domaine vérifié, le mode de test du fournisseur peut limiter les destinataires : il ne constitue pas un envoi commercial général. L’activation et les restrictions dépendent du compte fournisseur ; aucun compte Resend n’a été créé automatiquement et aucune livraison réelle n’a été testée. L’application affiche un message explicatif et propose le PDF si la messagerie n’est pas configurée.

L’ancien SMTP STARTTLS reste disponible avec `SMTP_HOST`, `SMTP_PORT` (587 par défaut), `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD`. Resend est prioritaire si sa clé est définie. Les ports SMTP peuvent être bloqués par l’hébergement ; privilégier HTTPS sur Render gratuit.
