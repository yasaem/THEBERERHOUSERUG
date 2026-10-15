# Exploiter Bazar comme éditeur SaaS

Le parcours commercial est **éditeur → entreprise cliente → boutiques → utilisateurs**. Les clients ne peuvent pas s’inscrire librement par défaut.

## Votre compte éditeur

Initialisez votre compte depuis un terminal de confiance, après installation :

```bash
.venv/bin/python scripts/create_platform_admin.py
```

Ou dans le conteneur serveur :

```bash
docker compose exec app python scripts/create_platform_admin.py
```

Le programme demande nom, e-mail et mot de passe (12 caractères minimum, saisie masquée). Aucun compte, tarif ou mot de passe commercial n’est préconfiguré. N’envoyez jamais votre mot de passe dans le chat. Le compte éditeur est distinct des entreprises et n’a pas accès aux stocks, ventes et données financières des clients depuis son écran d’administration.

Connectez-vous ensuite à l’application avec ce compte. Vous accédez à **Éditeur SaaS**.

## Vos formules

Cliquez sur **Nouvelle formule**. Définissez votre prix mensuel MAD, votre nombre maximal de boutiques et votre nombre maximal d’utilisateurs actifs. Les formules déjà créées restent immuables ; créez une nouvelle formule pour un autre tarif, puis affectez-la aux clients concernés. L’affectation ne modifie pas les périodes déjà payées et ne recalcule pas de prorata.

La formule d’essai fournie ne coûte rien, autorise 3 boutiques / 10 utilisateurs et dure 14 jours. Ce n’est pas un tarif commercial imposé. Une entreprise peut aussi essayer pendant 14 jours une formule commerciale choisie par vous. Les entreprises antérieures à cette évolution reçoivent un essai initial une seule fois ; redémarrer le serveur ne renouvelle pas cet essai.

## Créer un client

1. **Nouvelle entreprise** : nom de l’entreprise, nom de la boutique principale, nom/e-mail de son administrateur, formule et mot de passe provisoire de 12 caractères minimum.
2. Le serveur crée l’entreprise, son administrateur et sa boutique dans une transaction unique. Un e-mail déjà utilisé fait annuler toute la création.
3. Communiquez les accès au client par un canal sécurisé. Aucun envoi automatique de mot de passe n’est effectué.
4. À sa première connexion, le client doit remplacer le mot de passe provisoire. Avant cela, aucun stock ni donnée ERP n’est accessible.
5. Son administrateur gère ses sous-boutiques et ses utilisateurs, selon sa formule. Il ne peut pas créer d’autres entreprises ni accéder à l’administration SaaS.
6. Vous pouvez réinitialiser son accès sans connaître son mot de passe actuel : le nouveau mot de passe provisoire devra encore être remplacé et ses anciennes sessions seront révoquées.

## Encaisser un abonnement

Cette version gère les **règlements manuels** (virement, espèces, autre), pas des débits automatiques.

1. Choisissez la formule commerciale du client.
2. Une fois le paiement effectivement reçu, cliquez **Renouveler**.
3. Saisissez le nombre entier de mois (1 à 24), le montant reçu, le mode et la référence unique.
4. Le montant doit correspondre au prix de la formule multiplié par le nombre de mois. Pas de paiement partiel, de remise ni de changement de devise dans ce module.
5. Le serveur prolonge la couverture en mois calendaires depuis l’échéance actuelle ou depuis maintenant si elle est dépassée. Une année bissextile ou un mois plus court ne sont pas traités comme une durée arbitraire de 30 jours.
6. La même clé de validation ne crée pas de double règlement. Réutiliser une référence de virement pour le même client est refusé.

Les recettes SaaS sont séparées des ventes et commissions des bazars. L’historique n’est pas une facture fiscale d’abonnement ; sa conformité fiscale et les documents commerciaux associés doivent encore être définis.

Un paiement confirmé ne supprime **pas** une suspension manuelle. Réactivez explicitement le compte après avoir traité la raison de suspension. Réactiver un compte expiré ne prolonge pas son abonnement.

## Suspension, expiration et limites

L’accès est contrôlé côté serveur à chaque requête, y compris sur une session déjà ouverte. Un compte suspendu ou expiré conserve toutes ses données, mais les opérations ERP sont bloquées. Le client peut se connecter pour voir que son accès est en pause, se déconnecter ou sécuriser son mot de passe.

Les quotas sont vérifiés dans les transactions de création, pas seulement par l’interface. Réactiver un utilisateur consomme également une place. On ne peut pas affecter une formule dont les limites sont inférieures à l’utilisation actuelle. Les boutiques archivées/supprimées ne sont pas gérées ici : toutes les boutiques existantes comptent.

## Paiement automatique ultérieur

Le prestataire doit être choisi selon le pays d’immatriculation de votre société, les devises, les banques et les moyens de paiement acceptés. Ne supposez pas qu’un prestataire international permet l’ouverture d’un compte marocain. L’intégration nécessitera un compte marchand vérifié, des clés configurées dans les secrets et des webhooks signés et idempotents. Une page de retour de paiement ne doit jamais activer seule un abonnement.

Aucun paiement réel, prélèvement ni création de compte marchand n’a été exécuté. Les tarifs utilisés dans les tests sont uniquement des données de test.
