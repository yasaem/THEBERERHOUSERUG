# Guide utilisateur

**Langues :** choisissez Français ou English avant connexion ou dans la barre supérieure. Le choix est mémorisé dans le navigateur. Dans une facture, un second sélecteur choisit la langue du document sans changer l’interface. Les PDF et e-mails utilisent cette langue. Les données saisies restent inchangées.

1. Votre fournisseur crée votre entreprise et votre compte administrateur. Connectez-vous avec les accès provisoires puis choisissez votre mot de passe personnel (12 caractères minimum). Votre boutique principale est déjà créée. Si vous êtes l’éditeur, consultez [le guide SaaS](SAAS.md) pour initialiser votre compte et créer vos clients.
2. Dans **Boutiques**, ajoutez vos autres points de vente. Le filtre en haut change la vue ; aucune sélection signifie une consolidation de l’entreprise.
3. Dans **Produits & stock**, ajoutez vos articles ou cliquez sur **Importer**. Sélectionnez une boutique, un fichier CSV/Excel, associez les colonnes puis vérifiez l’aperçu. Nom, référence et quantité sont obligatoires. Les erreurs et doublons annulent tout l’import. Le classeur Excel doit avoir une première feuille standard, sans cellules fusionnées ni formules à recalculer.
4. Utilisez **Ajuster** pour corriger une quantité avec un motif ; **Modifier** ne change pas l’historique des ventes. L’archivage empêche les nouvelles ventes de l’article sans le supprimer.
5. Dans **Nouvelle vente**, choisissez une boutique. Ajoutez plusieurs lignes, sélectionnez des articles ou choisissez un article libre et sa désignation. Saisissez des quantités entières et des prix HT en MAD.
6. Complétez remise, TVA, shipping supporté, frais bancaires et montant reçu. Ajoutez les bénéficiaires de commissions. Pour les vendeurs, renseignez une enveloppe commune et des parts totalisant 100 %. Le champ de compte bénéficiaire rattache les gains à un vendeur connecté. Les autres partenaires n’ont pas besoin de compte.
7. Vérifiez le récapitulatif puis validez. Le stock, les commissions et le tableau de bord sont mis à jour dans une même transaction. Un double clic avec la même clé ne crée pas une seconde vente.
8. Dans **Ventes**, le bouton **＋** ajoute un encaissement partiel. Le bouton document ouvre la facture ; vous pouvez imprimer, télécharger le PDF ou l’envoyer si SMTP est configuré.
9. Dans **Commissions**, **Régler** enregistre un paiement du bénéficiaire, distinct du paiement client. Les dépenses et salaires utilisent le même principe.
10. Dans **Employés & salaires**, créez l’employé puis **Déclarer un salaire** pour chaque période. La rémunération de référence seule ne crée aucune charge. Déclarez une seule fois chaque salaire mensuel ; cette version ne bloque pas les doublons de période et n’établit pas de bulletin réglementaire.
11. **Rapports & statistiques** distingue charges dues et montants payés. Le mois sélectionné utilise les dates des opérations, pas un rapprochement bancaire.
12. Dans **Paramètres**, ajoutez les utilisateurs, leur rôle et leur boutique. Le propriétaire voit toute l’entreprise. Le responsable voit les données opérationnelles et financières de sa boutique. Le vendeur voit son stock sans coût d’achat, ses ventes et ses gains ; l’opérateur voit le stock sans coût d’achat et peut enregistrer des ventes.
13. Dans les informations de facturation, renseignez ICE, IF, adresse et logo. Les factures futures reprennent ces données ; les anciennes conservent leur instantané.

Les exports CSV respectent les données effectivement autorisées par le serveur. Ils sont compatibles avec un tableur utilisant le séparateur point-virgule. Les en-têtes des exports sont traduits et indiquent les montants en centimes MAD ; les colonnes de dates sont en UTC. Les identifiants servent à relier les lignes.

Une annulation restaure le stock une seule fois. Elle n’efface ni la vente ni les encaissements antérieurs. Ne l’utilisez pas comme substitut à une procédure d’avoir ou de remboursement réglementaire.
