# Couverture et recette

Cette livraison est une première version exécutable. Les points ouverts du cahier des charges ne sont pas traités comme des choix métier validés.

| Scénario | État |
|---|---|
| Deux entreprises, données isolées | Test automatisé |
| Plusieurs boutiques, responsable limité à sa boutique | Test automatisé |
| Import Excel/CSV, aperçu, colonnes, doublons | API testée ; interface disponible |
| Stock, ajustements, archivage | API testée et parcours navigateur |
| Vente multi-articles et hors catalogue | API et parcours navigateur |
| Shipping déduit, commissions indépendantes, partage vendeurs | Tests financiers, dont exemple 3 640 MAD |
| Arrondis sans double comptabilisation de l’enveloppe | Test au centime |
| Paiement client et commission partiels | Tests automatisés |
| Annulation et double validation | Tests de stock, idempotence et commissions |
| PDF A4, TVA, remise, informations historiques et logo | Génération PDF testée ; logo disponible dans les paramètres |
| Envoi par e-mail | Implémenté ; service SMTP externe à configurer et tester |
| Dépenses et salaires engagés/payés | Modules disponibles, règlements par API |
| Tableau de bord et consolidation en MAD | Interface et calculs disponibles |
| Vendeur/opérateur sans coûts confidentiels | Tests d’autorisation |
| Déconnexion, révocation, CSRF | Contrôles serveur, tests |
| Responsive ordinateur et mobile | Parcours Chromium à 1440 et 390 pixels |
| Interface et factures français/anglais | Parcours Chromium, PDF bilingues, choix mémorisé et e-mails simulés testés |
| Sauvegarde | Commande avec vérification d’intégrité |

## Écarts et extensions nécessaires

- Pas d’administration globale SaaS (entreprises actives/inactives, limites, abonnements). L’inscription crée une entreprise indépendante et un propriétaire.
- MAD uniquement. EUR/USD, conversions et historiques de taux nécessitent des règles validées avant consolidation.
- Vendeurs : parts en pourcentage d’une enveloppe commune, taux ou fixe ; pas d’interface de pondération ou de répartition par montants individuels.
- TVA globale 0/10/20 %, remise globale HT. Pas de taux personnalisés, taxes par ligne ni shipping refacturé au client.
- Numérotation `F-<identifiant vente>` de gestion, sans promesse de conformité fiscale. Pas d’avoir ni de remboursement ou retour partiel.
- Une boutique affectée par compte non propriétaire ; pas d’affectation multiple ni de permissions personnalisées.
- Clients et partenaires : fiches, sans rapprochement automatique des ventes à une relation client ni historique complet de règlements par fiche.
- Salaires de gestion, sans paie légale. Déclaration mensuelle manuelle, sans unicité automatique par période.
- CSV pour les exports, pas de génération de classeur XLSX. Excel en import : première feuille standard, pas de macros, `.xls` ni recalcul de formules.
- Pas de photos d’articles, justificatifs, échéancier, brouillons, transferts, notifications, interface arabe ou fonctionnement hors ligne.
- Pas de pagination serveur ni benchmark à grand historique ; serveur HTTP de développement, pas de migration PostgreSQL.
- Sauvegarde disponible, mais planification, copie externe, restauration opérationnelle et HTTPS relèvent du déploiement.

## Recette manuelle conseillée

Créer deux entreprises et deux boutiques dans l’une ; importer le fichier exemple ; créer un vendeur affecté à une boutique ; réaliser une vente avec deux articles et une ligne libre ; ajouter guide et agence plus deux vendeurs ; vérifier le calcul et le stock ; payer une partie du client puis une commission ; télécharger le PDF ; déclarer un salaire ; consulter les résultats ; vérifier les accès avec le compte vendeur. Annuler une autre vente sans commission payée et contrôler la restitution des quantités. Valider ensuite les règles fiscales et les écarts ci-dessus avant commercialisation.
