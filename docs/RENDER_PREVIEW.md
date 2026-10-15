# Essayer sur le web sans acheter de domaine ou de VPS

Le dépôt contient un Blueprint `render.yaml` pour un **aperçu gratuit Render**. Render attribue automatiquement une adresse HTTPS `*.onrender.com` après déploiement ; aucune adresse réelle n’est connue avant sa création.

[Ouvrir le déploiement Render](https://render.com/deploy?repo=https://github.com/yasaem/THEBERERHOUSERUG)

1. Connectez-vous à Render ou créez votre compte. Si le dépôt GitHub est privé, autorisez Render à y accéder avec votre compte GitHub. L’authentification Git de l’environnement Codex ne connecte pas automatiquement Render.
2. Vérifiez que le service utilise le plan **Free**. Ne sélectionnez pas de plan payant pour ce test. La disponibilité, les limites et les éventuelles vérifications de compte dépendent de Render.
3. Renseignez `BAZAR_PUBLISHER_EMAIL` et `BAZAR_PUBLISHER_PASSWORD` dans les champs privés du déploiement. Choisissez un mot de passe de 12 caractères minimum ; ne l’envoyez pas dans le chat et ne le commitez pas. Vous pouvez modifier le nom d’affichage `BAZAR_PUBLISHER_NAME`.
4. Lancez le déploiement. Le script initialise le compte éditeur une seule fois dans la base présente, ferme l’inscription publique, active les cookies Secure et démarre Gunicorn. Aucun mot de passe par défaut n’est fourni.
5. Ouvrez l’adresse HTTPS affichée par Render, connectez-vous avec les accès que vous avez choisis et créez des entreprises de test. La langue français/anglais est disponible.

## Limites à connaître avant l’essai

Le disque SQLite d’un service Free est **éphémère**. Les comptes et opérations peuvent être perdus après arrêt, redéploiement ou remplacement du service. Le compte éditeur est recréé depuis vos paramètres sécurisés si la base disparaît. Un compte existant n’est pas réinitialisé simplement parce qu’un secret de déploiement est changé.

L’interface affiche une bannière « données temporaires ». N’y saisissez pas de vraies données clients et ne vendez pas cette instance comme un service de production. Le service gratuit peut se mettre en veille ; l’ouverture peut demander un délai de redémarrage.

Cet aperçu n’utilise ni votre domaine ni votre compte Cloudflare, et n’exige pas de VPS. Il nécessite cependant votre authentification auprès de Render pour créer la ressource. Aucun déploiement Render réel n’a encore été exécuté depuis cette session.

Pour une version commerciale persistante, suivez `CLOUDFLARE.md` ou choisissez un hébergement avec stockage durable. La préparation de l’aperçu n’ajoute aucun prélèvement ni paiement automatique.
