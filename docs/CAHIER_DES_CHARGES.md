# CAHIER DES CHARGES FONCTIONNEL
## Application SaaS de gestion des bazars et commerces

**Projet :** ERP Bazar Management  
**Version :** 1.0 — Spécifications fonctionnelles  
**Marché initial :** Maroc  
**Plateforme :** Application web responsive (ordinateur, tablette, mobile)  
**Architecture :** SaaS multi-entreprises et multi-boutiques

---

# 1. PRÉSENTATION DU PROJET

## 1.1. Contexte

Le projet consiste à développer une application web ERP (Enterprise Resource Planning) destinée principalement aux bazars, boutiques artisanales et commerces touristiques au Maroc.

Ces établissements commercialisent différents types de marchandises : tapis, objets artisanaux, décoration, textiles, bijoux, poteries et autres articles.

Leur activité implique souvent plusieurs intervenants dans une vente : vendeurs, guides touristiques, agences, chauffeurs et responsables de boutique.

L'application doit permettre de centraliser et d'automatiser la gestion commerciale, financière et administrative de ces établissements.

## 1.2. Objectifs

L'application doit permettre :

- La gestion de plusieurs entreprises indépendantes.
- La gestion de plusieurs boutiques par entreprise.
- Le suivi des marchandises et du stock.
- L'enregistrement des ventes.
- Le calcul automatique des commissions.
- La création et l'impression de factures.
- Le suivi des paiements et des dépenses.
- Le suivi des salaires du personnel.
- Le calcul de la rentabilité réelle.
- L'analyse mensuelle des performances.
- La gestion des utilisateurs et de leurs permissions.

L'objectif principal est de fournir aux propriétaires une vue précise de leur activité, sans recourir à plusieurs fichiers Excel.

# 2. ARCHITECTURE MULTI-ENTREPRISES

## 2.1. Fonctionnement SaaS

L'application sera accessible en ligne et utilisée par plusieurs entreprises clientes.

Chaque entreprise dispose de son environnement indépendant.

**Exemple :**

Entreprise A :
- Bazar Marrakech Centre
- Bazar Guéliz
- Bazar Médina

Entreprise B :
- Bazar Atlas
- Bazar Essaouira

Les données de l'entreprise A ne doivent jamais être accessibles à l'entreprise B.

## 2.2. Gestion des entreprises

Un administrateur global doit pouvoir :

- Créer une entreprise.
- Modifier les informations de l'entreprise.
- Activer ou désactiver un compte.
- Consulter les entreprises inscrites.
- Gérer les accès à la plateforme.
- Définir les limites éventuelles d'utilisation.

## 2.3. Gestion des boutiques

Chaque entreprise doit pouvoir :

- Créer plusieurs boutiques.
- Définir le nom, l'adresse et les coordonnées.
- Ajouter un logo.
- Affecter des employés.
- Gérer le stock de chaque boutique.
- Suivre les ventes et les dépenses par boutique.
- Consulter les résultats consolidés de toutes ses boutiques.

Les données des boutiques sont séparées opérationnellement, mais le propriétaire peut accéder à une vue consolidée.

# 3. GESTION DES UTILISATEURS ET PERMISSIONS

## 3.1. Rôles

| Rôle | Autorisations |
|---|---|
| Super-administrateur | Administration globale de la plateforme SaaS |
| Propriétaire / Administrateur entreprise | Accès à toutes les boutiques, ventes, finances et employés de son entreprise |
| Responsable boutique | Gestion de sa boutique selon les permissions attribuées |
| Vendeur | Consultation de ses ventes et commissions |
| Comptable / Opérateur | Consultation du stock et ajout de ventes, avec accès limité |
| Autre employé | Permissions personnalisables |

## 3.2. Gestion des accès

Le propriétaire doit pouvoir :

- Créer des comptes utilisateurs.
- Affecter un utilisateur à une ou plusieurs boutiques.
- Modifier les rôles.
- Activer et désactiver des comptes.
- Réinitialiser les accès.
- Attribuer des autorisations par fonctionnalité.

Les permissions doivent être gérées côté serveur et pas uniquement par masquage des boutons.

**Règle importante :** le profil Comptable / Opérateur défini initialement doit rester limité à la consultation du stock et à l'ajout des ventes, sans accès automatique à la totalité des résultats financiers ou aux données confidentielles.

# 4. GESTION DES ARTICLES ET DU STOCK

## 4.1. Catalogue des articles

Chaque article doit pouvoir contenir :

- Identifiant unique.
- Référence interne.
- Nom de l'article.
- Description.
- Catégorie / type personnalisable.
- Boutique de rattachement.
- Prix d'achat.
- Prix de vente indicatif.
- Quantité disponible.
- Photos (fonction souhaitable).
- État : actif / archivé.

Le propriétaire doit pouvoir créer ses propres catégories, sans se limiter à une liste prédéfinie.

Exemples : tapis, bijoux, décoration, cuir, poterie, vêtements, objets divers.

## 4.2. Fonctionnalités du stock

- Ajouter un article.
- Modifier un article.
- Archiver un article.
- Ajouter une quantité au stock.
- Corriger une quantité.
- Consulter les stocks par boutique.
- Rechercher et filtrer les articles.
- Consulter la valeur du stock.
- Exporter les données.
- Importer les articles depuis Excel.

## 4.3. Mouvements de stock

L'application doit enregistrer les mouvements :

- Entrée de marchandise.
- Vente.
- Ajustement manuel.
- Retour de marchandise.
- Correction d'inventaire.

Chaque mouvement doit conserver une date, une quantité, un motif et l'utilisateur responsable.

## 4.4. Déduction automatique

Lorsqu'une vente est validée, les quantités vendues sont automatiquement déduites du stock.

En cas d'annulation ou de retour, le système doit pouvoir rétablir les quantités appropriées.

## 4.5. Articles hors stock

L'application doit obligatoirement permettre de vendre un article qui n'existe pas dans le catalogue.

L'utilisateur peut saisir librement :

- Désignation.
- Description.
- Quantité.
- Prix de vente.
- Coût d'achat si connu.

Cette vente doit être prise en compte dans les chiffres d'affaires et calculs financiers sans imposer la création préalable d'une fiche stock.

## 4.6. Exclusion

**Le développement d'un module de commande de marchandises auprès des fournisseurs n'est pas demandé.**

Le besoin porte sur le suivi, l'import et l'ajustement des stocks existants.

# 5. GESTION DES VENTES

## 5.1. Enregistrement d'une vente

Une vente peut contenir :

- Numéro unique de vente.
- Date et heure.
- Entreprise et boutique.
- Client, si renseigné.
- Un ou plusieurs articles.
- Quantités.
- Prix unitaires.
- Réductions.
- Montant total.
- Devise.
- Frais de livraison.
- Frais bancaires.
- Vendeurs participants.
- Guides, agences ou chauffeurs concernés.
- Moyen de paiement.
- Statut de règlement.
- Commentaires internes.

## 5.2. Vente multi-articles

Une vente peut regrouper plusieurs articles dans une seule opération.

Chaque ligne doit conserver son prix de vente et son coût d'achat pour permettre un calcul correct des marges.

## 5.3. Ventes avec plusieurs vendeurs

Une vente peut être attribuée à plusieurs vendeurs.

La répartition peut être :

- Égalitaire.
- Selon des pourcentages personnalisés.
- Selon des montants fixes.
- Selon une pondération définie.

**Exemple :**

Vente de 10 000 MAD avec trois vendeurs :

- Vendeur A : 50 %.
- Vendeur B : 30 %.
- Vendeur C : 20 %.

Le calcul des commissions individuelles doit respecter cette répartition, sans double comptabilisation.

## 5.4. Cycle de vie des ventes

Statuts proposés :

- Brouillon.
- Validée.
- Partiellement payée.
- Payée.
- Annulée.
- Remboursée.

Les annulations doivent être tracées. Une vente annulée ne doit plus contribuer au chiffre d'affaires net.

# 6. GESTION DES COMMISSIONS

Ce module constitue l'une des fonctionnalités principales du projet.

## 6.1. Intervenants commissionnés

Une vente peut impliquer simultanément :

- Un ou plusieurs vendeurs.
- Un guide touristique.
- Une agence touristique.
- Un chauffeur.

Le nombre d'intervenants doit être flexible.

## 6.2. Types de commissions

Chaque commission peut être définie :

- En pourcentage.
- En montant fixe.
- Dans une devise définie.

Les taux doivent pouvoir différer selon l'intervenant ou la vente.

## 6.3. Calcul des commissions

Le système doit calculer automatiquement les commissions.

**Règle métier déjà retenue : les frais de shipping/livraison doivent être retirés de l'assiette avant le calcul des commissions.**

Exemple illustratif :

| Élément | Montant |
|---|---:|
| Vente | 10 000 MAD |
| Shipping déductible | 500 MAD |
| Base de commission | 9 500 MAD |
| Guide : 10 % | 950 MAD |
| Agence : 5 % | 475 MAD |
| Vendeur : 3 % | 285 MAD |
| Total commissions | 1 710 MAD |

Dans cet exemple, les commissions sont calculées sur la même base de 9 500 MAD.

La formule précise devra tenir compte des remises, des taxes et des différentes natures de frais selon les paramètres validés.

## 6.4. Commissions avec intervenants multiples

Une même vente peut générer plusieurs commissions indépendantes.

Le système doit :

- Identifier tous les bénéficiaires.
- Déterminer l'assiette applicable.
- Calculer les montants dus.
- Répartir les commissions des vendeurs.
- Empêcher les répartitions incohérentes.
- Conserver le détail du calcul.

## 6.5. Suivi des commissions

Pour chaque intervenant :

- Liste des ventes concernées.
- Montant total gagné.
- Montant payé.
- Montant restant à payer.
- Historique des règlements.
- Filtres par boutique et période.

Un vendeur connecté doit pouvoir consulter ses propres ventes et ses propres gains, sans visualiser les commissions confidentielles d'autres employés.

## 6.6. Gestion des règlements

Le propriétaire doit pouvoir enregistrer le paiement d'une commission, qu'il soit total ou partiel.

Le paiement d'une commission ne doit pas être confondu avec le paiement de la vente par le client.

# 7. CLIENTS ET FACTURATION

## 7.1. Fichier clients

L'application doit pouvoir enregistrer :

- Nom / raison sociale.
- Coordonnées.
- Adresse.
- E-mail.
- Téléphone.
- Identifiants fiscaux utiles.
- Historique des achats.
- Historique des factures.

La saisie d'un client ne doit pas obligatoirement être imposée pour enregistrer une vente simple.

## 7.2. Création des factures

Une facture peut être générée à partir d'une vente.

Elle doit contenir :

- Logo du commerce.
- Nom et coordonnées de l'entreprise.
- Numéro de facture.
- Date.
- Coordonnées du client.
- Liste détaillée des articles.
- Quantités.
- Prix unitaires.
- Remises.
- Montants HT.
- TVA.
- Montants TTC.
- Livraison facturée.
- Total général.
- Montants payés et restants dus.
- Échéance si applicable.

## 7.3. Fiscalité et devises

L'application doit gérer, en fonction des paramètres fiscaux applicables :

- TVA à 0 %.
- TVA à 10 %.
- TVA à 20 %.
- Autres taux configurables si nécessaire.

Les devises initiales sont :

- MAD (dirham marocain).
- EUR (euro).
- USD (dollar américain).

Les informations fiscales de l'entreprise, notamment ICE et identifiants réglementaires applicables, doivent pouvoir apparaître sur les factures.

## 7.4. Fonctions de facturation

- Générer une facture PDF.
- Télécharger le PDF.
- Imprimer la facture.
- Envoyer la facture par e-mail.
- Retrouver une facture existante.
- Consulter le statut de paiement.
- Enregistrer les paiements partiels.
- Suivre les montants dus.

L'impression doit produire un document propre, correctement mis en page, notamment au format A4, sans éléments d'interface visibles.

## 7.5. Fiabilité

Les factures émises doivent conserver leurs montants historiques, même si le prix d'un article change ultérieurement.

Les factures validées ne doivent pas être supprimées sans trace. Les procédures de correction et d'avoir devront respecter les obligations légales applicables.

# 8. GESTION FINANCIÈRE ET RENTABILITÉ

## 8.1. Suivi des revenus

L'application doit pouvoir distinguer :

- Montant total des ventes.
- Ventes annulées ou remboursées.
- Chiffre d'affaires net.
- Montants encaissés.
- Créances clients.

## 8.2. Gestion des dépenses

L'utilisateur autorisé doit pouvoir enregistrer des dépenses.

Exemples :

- Salaires.
- Loyers.
- Électricité et eau.
- Frais bancaires.
- Transport.
- Shipping / livraison.
- Commissions.
- Frais administratifs.
- Autres charges.

Chaque dépense doit contenir une date, un montant, une catégorie, une boutique, une description et éventuellement un justificatif.

## 8.3. Frais bancaires

Les frais bancaires peuvent être associés directement à une vente.

Exemple : une commission bancaire de 2 % sur un paiement par carte.

Ces frais doivent être déduits du résultat de la vente et visibles séparément.

## 8.4. Calcul de la marge

Pour chaque vente, le système doit distinguer :

**Marge commerciale :**

Chiffre d'affaires hors taxes diminué du coût d'achat des marchandises vendues.

**Contribution nette de la vente :**

Marge commerciale diminuée des commissions, du shipping à la charge de l'entreprise, des frais bancaires et des autres coûts directement liés à la vente.

**Résultat de la période :**

Somme des contributions des ventes, diminuée des charges générales et salaires de la période.

Le système doit impérativement éviter de déduire deux fois les mêmes frais ou commissions.

## 8.5. Exemple de calcul

| Élément | Montant |
|---|---:|
| Chiffre d'affaires HT | 10 000 MAD |
| Coût des marchandises | − 4 000 MAD |
| Shipping supporté par la boutique | − 500 MAD |
| Commissions | − 1 710 MAD |
| Frais bancaires | − 150 MAD |
| Contribution nette de la vente | **3 640 MAD** |

Les charges fixes, comme les salaires et loyers, sont ensuite prises en compte dans le résultat global sur la période.

Les exemples chiffrés sont illustratifs, non des paramètres métier figés.

# 9. GESTION DES EMPLOYÉS ET DES SALAIRES

## 9.1. Fiche employé

- Identifiant.
- Nom et prénom.
- Boutique de rattachement.
- Poste.
- Date d'entrée.
- Statut actif / inactif.
- Salaire de référence.
- Paramètres de commission éventuels.

## 9.2. Suivi des salaires

L'application doit permettre :

- D'enregistrer les salaires dus.
- D'identifier les salaires déclarés.
- De suivre les salaires effectivement payés.
- D'enregistrer les dates de paiement.
- De suivre les paiements partiels.
- De visualiser les montants restant dus.
- De filtrer les charges salariales par mois ou boutique.

L'objectif est d'assurer un suivi de gestion. Le calcul automatique de la paie réglementaire marocaine n'est pas inclus dans le périmètre initial.

## 9.3. Performance des employés

Pour chaque vendeur :

- Nombre de ventes.
- Chiffre d'affaires généré.
- Commissions acquises.
- Commissions déjà payées.
- Commissions restant dues.
- Historique mensuel.

# 10. TABLEAUX DE BORD ET REPORTING

## 10.1. Tableau de bord propriétaire

Le propriétaire doit visualiser sur une période choisie :

- Chiffre d'affaires.
- Nombre de ventes.
- Montants encaissés.
- Montants restant à encaisser.
- Coûts des marchandises vendues.
- Total des commissions.
- Frais de livraison.
- Frais bancaires.
- Salaires déclarés / dus.
- Salaires payés.
- Autres dépenses.
- Résultat net de gestion.
- Valeur du stock.

## 10.2. Analyse mensuelle

L'application doit offrir une synthèse mensuelle permettant de comparer :

- Ventes.
- Dépenses.
- Commissions.
- Salaires.
- Rentabilité.

L'utilisateur peut sélectionner un mois, une année, une boutique ou l'ensemble de l'entreprise.

## 10.3. Vue entreprise / boutique

Les tableaux de bord doivent permettre :

- Une vue globale consolidée.
- Une vue détaillée par boutique.
- Une comparaison des performances entre boutiques.
- Une analyse des ventes par catégorie.
- Une analyse des vendeurs et des intervenants.

## 10.4. Vue vendeur

Le vendeur accède uniquement aux informations autorisées :

- Ses ventes.
- Son chiffre d'affaires attribué.
- Ses commissions.
- Ses règlements.
- Son historique de performance.

## 10.5. Exports

Les principaux tableaux devront pouvoir être exportés en Excel ou CSV.

Les rapports de synthèse devront également pouvoir être imprimés ou exportés en PDF (fonction complémentaire recommandée).

# 11. IMPORTATION ET EXPORTATION DES DONNÉES

## 11.1. Import Excel

L'utilisateur doit pouvoir importer un fichier contenant des articles et des quantités.

L'import doit comprendre :

- Sélection du fichier.
- Association des colonnes.
- Aperçu des données.
- Contrôle des erreurs.
- Identification des doublons.
- Validation avant intégration.
- Compte rendu d'import.

## 11.2. Export

Exports attendus :

- Liste des stocks.
- Liste des ventes.
- Liste des clients.
- Factures.
- Commissions.
- Dépenses.
- Salaires.
- Rapports financiers.

Les exports doivent respecter les permissions de l'utilisateur.

# 12. INTERFACE UTILISATEUR

## 12.1. Principes

L'interface doit être :

- Moderne et professionnelle.
- Facile à comprendre.
- Adaptée aux utilisateurs non techniques.
- Rapide pour enregistrer une vente.
- Responsive sur ordinateur, tablette et smartphone.
- Organisée autour de menus simples.

## 12.2. Navigation principale

Menu envisagé :

1. Tableau de bord.
2. Ventes.
3. Produits et stock.
4. Clients.
5. Factures.
6. Guides, agences et partenaires.
7. Commissions.
8. Dépenses.
9. Employés et salaires.
10. Rapports et statistiques.
11. Boutiques.
12. Paramètres.

L'affichage dépend du rôle et des permissions.

# 13. EXIGENCES TECHNIQUES

## 13.1. Architecture

Le développeur est libre de proposer une technologie adaptée, sous réserve de respecter :

- Une architecture web client / serveur.
- Une base de données relationnelle.
- Une API sécurisée.
- Une séparation stricte des entreprises.
- Une gestion robuste des transactions financières et du stock.
- Une conception modulaire et maintenable.

## 13.2. Sécurité

Exigences minimales :

- Authentification sécurisée.
- Gestion des sessions.
- Contrôle des permissions côté serveur.
- Isolation des données entre entreprises.
- Protection des informations sensibles.
- Communication HTTPS.
- Sauvegardes régulières.
- Journalisation des opérations critiques.

## 13.3. Intégrité des données

Les opérations doivent rester cohérentes.

Exemples :

- Une vente ne doit pas être enregistrée deux fois après un double clic.
- Une commission ne doit pas être calculée deux fois.
- Une annulation doit corriger les indicateurs et le stock.
- Une modification d'article ne doit pas modifier les anciennes ventes.
- Les règlements partiels doivent être historisés.

## 13.4. Performances

Les fonctionnalités courantes doivent rester fluides, même avec plusieurs boutiques et un historique important.

La consultation des tableaux de bord doit s'appuyer sur des requêtes optimisées et une pagination adaptée.

# 14. STRUCTURE DES DONNÉES ATTENDUE

Le développeur devra concevoir un modèle relationnel comprenant notamment les entités suivantes :

| Entité | Fonction |
|---|---|
| Entreprises | Sociétés clientes de la plateforme |
| Boutiques | Points de vente des entreprises |
| Utilisateurs | Comptes d'accès |
| Rôles / Permissions | Autorisations fonctionnelles |
| Employés | Informations du personnel |
| Articles | Catalogue des marchandises |
| Catégories | Types d'articles personnalisables |
| Stocks | Quantités par boutique |
| Mouvements de stock | Historique des entrées et sorties |
| Clients | Fichier clients |
| Ventes | Opérations commerciales |
| Lignes de vente | Articles vendus et leurs prix historiques |
| Participations à la vente | Répartition entre vendeurs |
| Intervenants | Guides, agences, chauffeurs et autres bénéficiaires |
| Commissions | Montants calculés par bénéficiaire |
| Paiements de commissions | Règlements et soldes |
| Factures | Documents de facturation |
| Paiements clients | Encaissements |
| Dépenses | Charges de gestion |
| Salaires | Montants dus, déclarés et payés |
| Paramètres fiscaux | Taxes, devises et informations légales |
| Journal d'audit | Historique des opérations sensibles |

Cette liste est conceptuelle : le modèle définitif et les relations seront conçus par le développeur.

# 15. PARCOURS MÉTIER — EXEMPLE COMPLET

**Scénario : un touriste achète plusieurs articles dans un bazar.**

1. Le vendeur ouvre l'écran Nouvelle vente.
2. Il sélectionne sa boutique.
3. Il ajoute deux articles existants en stock.
4. Il ajoute éventuellement un troisième article libre.
5. Il renseigne les prix et la remise.
6. Il sélectionne les vendeurs participant à l'opération.
7. Il associe un guide touristique et éventuellement une agence ou un chauffeur.
8. Il renseigne les commissions applicables.
9. Il ajoute les frais de shipping et les frais bancaires.
10. Le système affiche un récapitulatif comprenant les montants, commissions et la rentabilité estimée.
11. Le vendeur valide la vente.
12. Le stock des articles concernés est mis à jour.
13. Les commissions dues sont enregistrées.
14. Le paiement client est enregistré selon son statut.
15. Une facture professionnelle peut être générée, imprimée ou envoyée par e-mail.
16. Les tableaux de bord de la boutique et de l'entreprise sont automatiquement mis à jour.
17. Les bénéficiaires autorisés peuvent consulter leurs commissions.
18. Le propriétaire peut ultérieurement enregistrer les paiements des commissions.

Toutes les étapes doivent être traçables.

# 16. RÈGLES MÉTIER PRIORITAIRES

**RM-01 — Isolation des entreprises**  
Une entreprise ne peut jamais accéder aux données d'une autre entreprise.

**RM-02 — Gestion multi-boutiques**  
Les stocks et opérations sont suivis par boutique, avec consolidation au niveau entreprise.

**RM-03 — Stock**  
Toute vente validée comportant des articles stockés doit produire les mouvements correspondants.

**RM-04 — Articles libres**  
Une vente peut être réalisée sans que tous les articles existent dans le catalogue.

**RM-05 — Commissions**  
Une vente peut comporter plusieurs bénéficiaires et plusieurs méthodes de calcul.

**RM-06 — Shipping**  
Les frais de shipping déductibles sont exclus de l'assiette de calcul des commissions.

**RM-07 — Frais bancaires**  
Les frais bancaires sont identifiés séparément et pris en compte dans la rentabilité.

**RM-08 — Historisation**  
Toute vente doit conserver ses prix, coûts et paramètres de commission au moment de sa validation.

**RM-09 — Confidentialité**  
Un vendeur ne peut accéder qu'aux données relevant de ses permissions.

**RM-10 — Commissions et paiements**  
Une commission calculée n'est pas automatiquement considérée comme payée.

**RM-11 — Gestion mensuelle**  
L'application doit distinguer chiffre d'affaires, encaissements, dépenses engagées et dépenses payées.

**RM-12 — Absence de commandes fournisseurs**  
La gestion des bons de commande d'approvisionnement est hors périmètre initial.

# 17. POINTS À DÉFINIR AVANT LE DÉVELOPPEMENT

Certains choix complémentaires nécessiteront une validation fonctionnelle :

- Les règles exactes de calcul des commissions lorsque la vente comporte TVA, remise et plusieurs devises.
- La gestion des transferts de marchandises entre boutiques.
- Les seuils d'alerte sur les stocks.
- La méthode de conversion des devises et l'historisation des taux.
- La numérotation réglementaire des factures et les règles d'avoir.
- Le traitement des retours partiels et remboursements.
- L'affectation des charges générales entre plusieurs boutiques.
- Les modalités d'abonnement et de facturation des entreprises clientes du SaaS.
- La nécessité d'une interface multilingue (français, arabe, anglais).
- L'éventuelle utilisation sans connexion Internet.

Ces points ne doivent pas être considérés comme déjà validés dans le périmètre initial.

# 18. LIVRABLES ATTENDUS DU DÉVELOPPEUR

Le prestataire devra fournir :

1. Une proposition d'architecture technique.
2. Une maquette des principales interfaces.
3. Un schéma de base de données.
4. Une application web opérationnelle.
5. Une API backend sécurisée.
6. Les modules fonctionnels demandés.
7. La génération PDF des factures.
8. Les fonctionnalités d'import/export.
9. Les tests des calculs financiers et des commissions.
10. Les tests des permissions et de l'isolation multi-entreprises.
11. Les procédures de déploiement et de sauvegarde.
12. Le code source et la documentation technique.
13. Une documentation utilisateur.
14. Une phase de recette et de correction des anomalies.

# 19. CRITÈRES D'ACCEPTATION

Le projet sera considéré comme fonctionnel lorsque les scénarios suivants pourront être exécutés avec succès :

- Créer deux entreprises et vérifier l'isolation complète de leurs données.
- Créer plusieurs boutiques sous une même entreprise.
- Importer et ajuster des articles en stock.
- Enregistrer une vente comportant plusieurs articles, dont un article hors stock.
- Calculer les commissions de plusieurs vendeurs, d'un guide et d'une agence.
- Vérifier la déduction du shipping avant le calcul des commissions.
- Générer une facture PDF avec TVA, remise et logo.
- Imprimer et envoyer une facture par e-mail.
- Enregistrer un paiement client partiel.
- Enregistrer un paiement de commission partiel.
- Suivre des salaires déclarés et payés.
- Afficher le résultat financier mensuel d'une boutique.
- Afficher le résultat consolidé d'une entreprise.
- Vérifier qu'un vendeur ne voit pas les données financières non autorisées.
- Annuler une vente et vérifier la cohérence du stock, des commissions et des indicateurs.

# 20. CONCLUSION

Cette application doit être conçue comme un ERP SaaS spécialisé dans le fonctionnement réel des bazars et commerces touristiques.

La valeur principale de la solution réside dans l'intégration de la gestion commerciale, du stock, des intervenants, des commissions, des dépenses, des salaires et de la rentabilité.

Le système doit être suffisamment simple pour une utilisation quotidienne dans une boutique, tout en offrant au propriétaire une vision financière complète et fiable de l'ensemble de ses établissements.

**Priorité : un logiciel simple à utiliser, avec des calculs financiers exacts, une traçabilité complète et une architecture permettant une commercialisation SaaS auprès de plusieurs entreprises.**
