# Cadre adaptatif de questions pour un projet numérique

## Sommaire

- Dimensionner le parcours
- Choisir le type de réponse
- Rechercher sans fragiliser une décision
- Tour d'orientation
- Triage des risques
- Tour fonctionnel et arbitrage
- Tour technique
- Routage par famille de projet
- Résoudre les réponses ambiguës

## Dimensionner le parcours

Ne jamais appliquer une taille fixe ni supposer que le parcours complet est nécessaire.

- **Idée vague** : commencer par 5 à 12 questions d'orientation, majoritairement ouvertes. Attendre les réponses avant de proposer des fonctions.
- **Idée intermédiaire** : poser généralement 8 à 25 questions ciblées sur les zones manquantes.
- **Idée précise** : reformuler les acquis, puis approfondir les 5 à 20 décisions réellement ouvertes.
- **Projet complexe ou demande approfondie** : répartir les questions en plusieurs tours, idéalement moins de 40 par fiche.
- **Demande courte** : limiter le premier tour aux décisions qui changent le plus le résultat et accepter de s'arrêter après l'exploration.

La longueur dépend du risque, du nombre de publics, des plateformes, des intégrations et de l'exploitation visée. Expliquer brièvement la raison de chaque nouveau tour.

## Choisir le type de réponse

Le format V2 accepte six types. Toujours renseigner `type` dans le JSON.

| Type | Usage | Valeur exportée |
|---|---|---|
| `open` | Découvrir un besoin, un contexte ou un exemple | texte |
| `decision` | Valider une proposition atomique | identifiant d'un choix |
| `single_choice` | Choisir une option mutuellement exclusive | identifiant d'un choix |
| `multi_choice` | Retenir plusieurs éléments indépendants | liste d'identifiants |
| `scale` | Mesurer importance, fréquence, tolérance ou confiance | nombre |
| `ranking` | Forcer un arbitrage entre plusieurs priorités | liste ordonnée d'identifiants |

Employer Oui/Non/Peut-être uniquement pour une proposition déjà formulée. Une question comme « Quel problème voulez-vous résoudre ? » doit être `open`, jamais une décision Oui/Non.

Pour chaque proposition :

- exprimer une seule décision concrète;
- préciser la conséquence si le sens peut être ambigu;
- indiquer dans `needs_clarification` si un choix appelle une note;
- réserver `tone` à la présentation (`neutral`, `positive`, `warning`, `negative`), sans l'utiliser comme statut métier;
- proposer explicitement « Je ne sais pas », « Non applicable » ou « À décider plus tard » lorsque ces réponses sont légitimes.

Une note nuance la réponse mais ne doit pas remplacer une réponse ouverte. Éviter les formulations doubles telles que « rapide et sécurisé ».

## Rechercher sans fragiliser une décision

Identifier les inconnues que les préférences de l'utilisateur ne peuvent pas résoudre : règles d'une plateforme, faisabilité d'une API, réglementation, état de l'art, coût actuel ou comparaison de produits.

- Effectuer directement une vérification courte et ciblée.
- Annoncer les missions lorsqu'une recherche est répartie entre agents spécialisés.
- Demander une autorisation seulement en cas de coût, d'écriture externe, d'action distante sensible ou d'élargissement de périmètre.
- Ne pas transformer en hypothèse une recherche indispensable à une décision structurante.
- Archiver les sources dans `conception/sources.md` et distinguer faits vérifiés, inférences et inspirations.

## Tour d'orientation

Pour une idée vague, faire émerger la forme du projet avant sa solution :

1. Quel problème, désir ou résultat déclenche l'idée ?
2. Qui l'utiliserait ou en bénéficierait ?
3. Dans quelle situation et à quelle fréquence ?
4. Quelle est la plus petite preuve que l'idée fonctionne ?
5. Le résultat attendu ressemble-t-il à un site, une application, un jeu, un outil, une automatisation, un service ou un produit connecté ?
6. Qu'est-ce qu'il faut absolument éviter ?
7. Quels exemples sont appréciés ou rejetés, et pourquoi ?
8. L'usage est-il personnel, partagé, interne, public restreint ou grand public ?
9. Quelles contraintes sont déjà certaines ?
10. Quel niveau de sortie est attendu : exploration, cadrage ou plan complet ?

Commencer avec des réponses `open`, puis transformer les résultats en propositions atomiques lors du tour suivant. Ne pas introduire une plateforme ou une architecture avant d'avoir compris l'usage, sauf contrainte déjà certaine.

## Triage des risques structurants

Faire ce triage dès le premier tour. Une réponse positive peut justifier une recherche ou un prototype avant de figer le périmètre.

- Données personnelles, financières, médicales, de mineurs ou secrets métier.
- Paiement, identité forte, signature, conformité ou conservation légale.
- API, format, store, matériel ou fournisseur imposé.
- Fonctionnement hors ligne, synchronisation ou réseau instable.
- Intelligence artificielle dont l'erreur peut produire un dommage important.
- Charge, latence, disponibilité ou coût par utilisateur déterminants.
- Migration de données existantes ou impossibilité de retour arrière.
- Accessibilité obligatoire ou public utilisant des appareils contraints.

Marquer chaque risque : `à vérifier`, `bloquant`, `à traiter avant un segment` ou `différable`.

## Tour fonctionnel et arbitrage

Sélectionner uniquement les thèmes pertinents :

1. **Problème et résultat** : résultat observable, limites, échec acceptable.
2. **Utilisateurs** : public principal et secondaire, compétences, fréquence, contexte.
3. **Parcours essentiels** : déclencheur, action, résultat, erreur, reprise, notification.
4. **Fonctionnalités** : indispensables, importantes, différables et hors périmètre.
5. **Contenu et données** : saisie, import, production, partage, rétention, suppression.
6. **Collaboration** : rôles, permissions, validation, commentaires, historique, départ d'un membre.
7. **Règles métier** : états, quotas, exceptions, modération, arbitrage humain.
8. **Valeur et économie** : bénéfice, gratuité, abonnement, transaction, coût récurrent.
9. **Succès** : preuve d'utilité, qualité, adoption, fréquence de retour.
10. **Évolution** : extensions pressenties et compatibilités à préserver.

Ne pas laisser toutes les fonctions devenir prioritaires. Utiliser un `ranking`, une sélection limitée ou les niveaux suivants : indispensable, important, différable, refusé. Enregistrer le refus au même titre que l'acceptation.

## Tour technique

Inférer d'abord les choix déjà présents dans les documents et réponses. Ne demander leur précision que si elle manque : obligatoire, préféré ou envisagé.

Sans choix précis, présenter deux à quatre scénarios :

- **ce que c'est**, sans jargon;
- **adapté si**, avec un exemple proche de l'usage;
- **moins adapté si**, avec la limite décisive;
- **entretien**, faible à important;
- **coût probable**, sans inventer de montant;
- **réversibilité** et dépendance à un fournisseur;
- **recommandation**, reliée aux décisions déjà acceptées.

Clarifier uniquement ce qui s'applique :

- portée et ordre de grandeur des utilisateurs simultanés;
- navigateur, mobile, ordinateur, serveur, terminal ou objet connecté;
- en ligne, hors ligne, réseau local ou synchronisation différée;
- comptes, invitations, SSO, récupération et rôles;
- sensibilité, volume, pièces jointes, géolocalisation et rétention des données;
- partage, export, portabilité et suppression;
- services externes, matériel, formats, API et migration;
- navigateurs, appareils, langues et accessibilité;
- hébergement, disponibilité, journaux, surveillance, sauvegarde et restauration;
- budget, délai, équipe, compétences, licences et réglementation lorsqu'ils sont connus;
- distribution, stores, installateur et mises à jour;
- archivage, migration et réversibilité.

## Routage par famille de projet

### Site ou application web

Approfondir navigation, responsive, navigateurs, SEO si public, comptes, données, hébergement, disponibilité et déploiement.

### Application mobile ou ordinateur

Approfondir systèmes ciblés, hors-ligne, permissions, notifications, batterie, tailles d'écran, distribution, stores, signature et mises à jour.

### Outil interne ou automatisation

Approfondir rôles, audit, validation humaine, erreurs, reprise, intégrations, propriété des données, maintenance et désactivation.

### Jeu ou expérience interactive

Approfondir boucle principale, rythme, progression, durée de session, persistance, multijoueur, économie, contenu, communauté, triche et modération.

### IA ou produit data

Approfondir origine et droit d'usage des données, qualité, erreurs acceptables, évaluation, validation humaine, explicabilité, traçabilité, coût d'inférence, confidentialité et comportement de repli.

### Produit connecté

Approfondir alimentation, connectivité, installation, sécurité physique, panne réseau, micrologiciel, durée de vie, pièces remplaçables et conformité.

### Service public ou grand public

Approfondir inscription, récupération, abus, modération, consentement, accessibilité, disponibilité, charge, support, suppression des données et coût par utilisateur.

## Résoudre les réponses ambiguës

- Oui avec une restriction : conserver Oui et intégrer la restriction à la décision interprétée.
- Non avec une alternative : refuser la proposition et créer une nouvelle proposition atomique.
- Peut-être sans note : demander le bénéfice recherché et l'inquiétude qui bloque.
- Réponse ouverte trop large : reformuler, puis proposer plusieurs décisions indépendantes.
- Deux décisions incompatibles : montrer le conflit et ses conséquences sans choisir silencieusement.
- Absence de réponse : ne pas assimiler à Non.
- Choix technique prématuré : préserver le besoin sous-jacent et marquer la solution comme hypothèse.
- Décision révisée : créer une nouvelle entrée qui référence l'ancienne avec `supersedes`; ne pas réécrire l'historique.
